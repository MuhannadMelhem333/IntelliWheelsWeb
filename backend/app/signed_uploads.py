"""Gated direct-upload protocol. Provider acceptance is required before rollout."""
import math
import os
import re
import time
from urllib.parse import urlsplit
import cloudinary.api
import cloudinary.utils
from flask import Blueprint, current_app, request, jsonify, g
from .db import get_db
from .security import require_auth, rate_limit
from .upload_quotas import reserve_upload, lock_upload_owner

bp = Blueprint('signed_uploads', __name__, url_prefix='/api/uploads')
FORMATS = {'image': ['jpg', 'png', 'gif', 'webp'], 'video': ['mp4', 'mov', 'avi', 'mkv', 'webm']}


def reply(body, status=200):
    response = jsonify(body)
    response.status_code = status
    response.headers['Cache-Control'] = 'no-store'
    return response


def provider_options():
    values = {name: os.environ.get(env, '') for name, env in (
        ('cloud_name', 'CLOUDINARY_CLOUD_NAME'), ('api_key', 'CLOUDINARY_API_KEY'), ('api_secret', 'CLOUDINARY_API_SECRET'))}
    if not all(values.values()) or not re.fullmatch(r'[A-Za-z0-9_-]+', values['cloud_name']):
        raise ValueError('Provider unavailable')
    return {**values, 'timeout': 10}


def enabled():
    return all(current_app.config[key] for key in ('SIGNED_UPLOADS_ENABLED', 'SIGNED_UPLOAD_PRESETS_VERIFIED', 'MEDIA_ASSET_LEDGER_ENABLED', 'UPLOAD_QUOTAS_ENABLED'))


def signed_parameters(intent, options):
    params = {'timestamp': intent['issued_at'], 'public_id': intent['public_id'],
              'upload_preset': intent['preset'], 'overwrite': 'false',
              'allowed_formats': ','.join(FORMATS[intent['resource_type']])}
    signature = cloudinary.utils.api_sign_request(params, options['api_secret'])
    return {'mode': 'direct', 'intentId': intent['id'],
            'uploadUrl': f"https://api.cloudinary.com/v1_1/{intent['cloud_name']}/{intent['resource_type']}/upload",
            'parameters': {**params, 'api_key': options['api_key'], 'signature': signature}}


def verified_metadata(metadata, intent):
    """Only accept observed server-to-server metadata, not browser JSON."""
    if metadata.get('public_id') != intent['public_id'] or metadata.get('resource_type') != intent['resource_type'] or metadata.get('type') != 'upload':
        raise ValueError('Asset identity mismatch')
    for key in ('bytes', 'width', 'height', 'version'):
        if type(metadata.get(key)) is not int or metadata[key] <= 0:
            raise ValueError('Missing bounded metadata')
    if not isinstance(metadata.get('asset_id'), str) or not metadata['asset_id']:
        raise ValueError('Missing immutable identity')
    if metadata['bytes'] > intent['max_bytes'] or max(metadata['width'], metadata['height']) > 10000 or metadata['width'] * metadata['height'] > 25000000:
        raise ValueError('Asset exceeds limits')
    if metadata.get('format') not in FORMATS[intent['resource_type']]:
        raise ValueError('Unsupported format')
    if intent['resource_type'] == 'video':
        duration = metadata.get('duration')
        if type(duration) not in (float, int) or not math.isfinite(duration) or not 0 < duration <= 120:
            raise ValueError('Invalid video duration')
    else:
        frames = metadata.get('pages', None if metadata['format'] in ('gif', 'webp') else 1)
        if type(frames) is not int or not 1 <= frames <= 100 or frames * metadata['width'] * metadata['height'] > 50000000:
            raise ValueError('Animation exceeds limits')
    url = metadata.get('secure_url', '')
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.netloc != 'res.cloudinary.com' or not parsed.path.startswith('/' + intent['cloud_name'] + '/'):
        raise ValueError('Unexpected delivery origin')
    return url


def completed_response(db, asset_id, owner_id):
    asset = db.execute('SELECT id, delivery_url, provider_id FROM media_assets WHERE id = ? AND owner_id = ?', (asset_id, owner_id)).fetchone()
    if not asset:
        raise ValueError('Completed asset unavailable')
    return reply({'success': True, 'assetId': asset['id'], 'url': asset['delivery_url'], 'path': asset['provider_id']})


@bp.route('/prepare', methods=['POST'])
@rate_limit(max_requests=60, window_seconds=60)
def prepare():
    user = require_auth()
    if not user:
        return reply({'success': False, 'error': 'Authentication required'}, 401)
    if not current_app.config['SIGNED_UPLOADS_ENABLED']:
        return reply({'mode': 'proxy'})
    if not enabled():
        return reply({'success': False, 'error': 'Direct uploads unavailable'}, 503)
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get('kind'), str) or data['kind'] not in FORMATS or not isinstance(data.get('requestKey'), str) or not re.fullmatch(r'[0-9a-f-]{32,36}', data['requestKey']):
        return reply({'success': False, 'error': 'Invalid upload request'}, 400)
    db = get_db()
    try:
        options = provider_options()
        old = db.execute('SELECT * FROM signed_upload_intents WHERE owner_id = ? AND request_key = ?', (user['id'], data['requestKey'])).fetchone()
        if old:
            if old['resource_type'] != data['kind'] or old['cloud_name'] != options['cloud_name']:
                return reply({'success': False, 'error': 'Upload request conflict'}, 409)
            if old['asset_id']:
                return reply({'mode': 'complete', 'intentId': old['id']})
            if time.time() - old['issued_at'] >= 3600:
                return reply({'success': False, 'error': 'Upload request expired; reconciliation required'}, 410)
            return reply(signed_parameters(old, options))
        config = current_app.config
        environment = config['SIGNED_UPLOAD_ENVIRONMENT']
        preset = config['SIGNED_UPLOAD_IMAGE_PRESET' if data['kind'] == 'image' else 'SIGNED_UPLOAD_VIDEO_PRESET']
        if environment not in ('development', 'staging', 'production') or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', preset):
            raise ValueError('Unverified upload configuration')
        maximum = config['IMAGE_UPLOAD_MAX_BYTES' if data['kind'] == 'image' else 'VIDEO_UPLOAD_MAX_BYTES']
        failure = reserve_upload(user['id'], data['kind'], maximum, commit=False)
        if failure is not None:
            return failure
        intent = {'id': g.upload_reservation_id, 'owner_id': user['id'], 'request_key': data['requestKey'],
                  'resource_type': data['kind'], 'cloud_name': options['cloud_name'], 'preset': preset,
                  'environment': environment, 'max_bytes': maximum, 'issued_at': int(time.time())}
        intent['public_id'] = f"intelliwheels/{environment}/{data['kind']}/{intent['id']}"
        db.execute('INSERT INTO signed_upload_intents (id, owner_id, request_key, resource_type, public_id, cloud_name, preset, environment, max_bytes, issued_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id',
                   tuple(intent[key] for key in ('id', 'owner_id', 'request_key', 'resource_type', 'public_id', 'cloud_name', 'preset', 'environment', 'max_bytes', 'issued_at'))).fetchone()
        result = signed_parameters(intent, options)
        db.commit()
        return reply(result)
    except Exception:
        db.rollback()
        current_app.logger.error('upload.prepare_failed')
        return reply({'success': False, 'error': 'Unable to prepare upload'}, 503)


@bp.route('/complete/<intent_id>', methods=['POST'])
@rate_limit(max_requests=30, window_seconds=60)
def complete(intent_id):
    user = require_auth()
    if not user:
        return reply({'success': False, 'error': 'Authentication required'}, 401)
    if not enabled() or not re.fullmatch(r'[0-9a-f]{32}', intent_id):
        return reply({'success': False, 'error': 'Upload not found'}, 404)
    db = get_db()
    try:
        intent = db.execute('SELECT * FROM signed_upload_intents WHERE id = ? AND owner_id = ?', (intent_id, user['id'])).fetchone()
        if not intent:
            return reply({'success': False, 'error': 'Upload not found'}, 404)
        if intent['asset_id']:
            return completed_response(db, intent['asset_id'], user['id'])
        options = provider_options()
        if options['cloud_name'] != intent['cloud_name']:
            raise ValueError('Provider changed')
        # No browser metadata or URL is used. No DB lock held during provider I/O.
        metadata = cloudinary.api.resource(intent['public_id'], resource_type=intent['resource_type'], type='upload', **options)
        url = verified_metadata(metadata, intent)
        lock_upload_owner(db, user['id'])
        latest = db.execute('SELECT asset_id FROM signed_upload_intents WHERE id = ?', (intent_id,)).fetchone()
        if latest['asset_id']:
            db.rollback()
            return completed_response(db, latest['asset_id'], user['id'])
        reservation = db.execute('SELECT owner_id, resource_type, source_bytes FROM upload_reservations WHERE id = ?', (intent_id,)).fetchone()
        if (not reservation or reservation['owner_id'] != user['id'] or
                reservation['resource_type'] != intent['resource_type'] or
                reservation['source_bytes'] != intent['max_bytes']):
            raise ValueError('Matching full-cap reservation required')
        db.execute('INSERT INTO media_assets (id, owner_id, provider, storage_namespace, resource_type, provider_id, delivery_url, source_bytes) VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING id',
                   (intent_id, user['id'], 'cloudinary', intent['cloud_name'], intent['resource_type'], intent['public_id'], url, metadata['bytes'])).fetchone()
        # Completion does not revoke the signed capability. Retain its full hold
        # until provider reconciliation; expiry alone must not release it either.
        # Ledger bytes + this hold deliberately over-count the expected object.
        db.execute('UPDATE signed_upload_intents SET asset_id = ?, provider_asset_id = ?, provider_version = ? WHERE id = ?',
                   (intent_id, metadata['asset_id'], metadata['version'], intent_id))
        db.commit()
        return completed_response(db, intent_id, user['id'])
    except Exception:
        db.rollback()
        current_app.logger.error('upload.completion_failed')
        return reply({'success': False, 'error': 'Unable to verify upload. Retry completion later.'}, 503)


@bp.route('/recovery', methods=['GET'])
@rate_limit(max_requests=30, window_seconds=60)
def recovery():
    """Bounded owner-only discovery; never signs, queries providers or refunds."""
    user = require_auth()
    if not user:
        return reply({'success': False, 'error': 'Authentication required'}, 401)
    if not enabled():
        return reply({'success': False, 'error': 'Upload recovery unavailable'}, 404)
    after = request.args.get('after', '')
    if after and not re.fullmatch(r'[0-9a-f]{32}', after):
        return reply({'success': False, 'error': 'Invalid recovery cursor'}, 400)
    try:
        rows = get_db().execute('''SELECT i.id, i.resource_type, i.issued_at, i.asset_id,
                                  r.id AS reservation_id FROM signed_upload_intents i
                                  LEFT JOIN upload_reservations r ON r.id=i.id AND r.owner_id=i.owner_id
                                  WHERE i.owner_id=? AND i.id>? ORDER BY i.id LIMIT 21''',
                               (user['id'], after)).fetchall()
        now = time.time()
        entries = [{'intentId': row['id'], 'kind': row['resource_type'],
                    'state': 'completed' if row['asset_id'] else 'pending',
                    'signatureExpired': now - row['issued_at'] >= 3600,
                    'quotaHeld': row['reservation_id'] is not None,
                    'assetId': row['asset_id']} for row in rows[:20]]
        return reply({'success': True, 'uploads': entries,
                      'nextCursor': rows[19]['id'] if len(rows) > 20 else None})
    except Exception:
        current_app.logger.error('upload.recovery_failed')
        return reply({'success': False, 'error': 'Upload recovery temporarily unavailable'}, 503)
