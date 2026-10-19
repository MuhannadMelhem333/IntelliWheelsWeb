"""Upload provenance only. Not listing association, a quota, or deletion authority."""
import uuid
import re
import json
from urllib.parse import urljoin
from flask import current_app, jsonify, request
from .db import get_db
from .listing_media import InvalidListingMedia, validate_listing_media
from .upload_quotas import consume_reservation, lock_upload_owner


def ledger_enabled():
    return current_app.config['MEDIA_ASSET_LEDGER_ENABLED']


def ledger_unavailable():
    response = jsonify({'success': False, 'error': 'Upload registration is unavailable. Please try again later.'})
    response.status_code = 503
    response.headers['Cache-Control'] = 'no-store'
    return response


def owned_asset_response(asset_id, owner_id):
    missing = {'success': False, 'error': 'Asset not found'}
    if not ledger_enabled() or not re.fullmatch(r'[0-9a-f]{32}', asset_id):
        return jsonify(missing), 404
    db = None
    try:
        db = get_db()
        row = db.execute(
            'SELECT id, resource_type, delivery_url, source_bytes FROM media_assets WHERE id = ? AND owner_id = ?',
            (asset_id, owner_id),
        ).fetchone()
    except Exception:
        _rollback(db)
        current_app.logger.error('upload.asset_lookup_failed')
        return ledger_unavailable()
    if row is None:
        return jsonify(missing), 404
    response = jsonify({'success': True, 'asset': {
        'id': row['id'], 'type': row['resource_type'], 'url': row['delivery_url'], 'sourceBytes': row['source_bytes'],
    }})
    response.headers['Cache-Control'] = 'no-store'
    return response


def check_ledger_ready():
    """Fail before storage if rollout was enabled without applying its migration."""
    if not ledger_enabled():
        return True
    db = None
    try:
        db = get_db()
        db.execute('SELECT id, owner_id, provider, storage_namespace, resource_type, provider_id, delivery_url, source_bytes, created_at FROM media_assets WHERE 1 = 0')
        return True
    except Exception:
        _rollback(db)
        current_app.logger.error('upload.ledger_unavailable')
        return False


def _rollback(db):
    if db is not None:
        try:
            db.rollback()
        except Exception:
            current_app.logger.error('upload.ledger_rollback_failed')


def finish_upload(payload, *, owner_id, provider, namespace, kind, provider_id, source_bytes):
    """Record only server-observed upload results; never accept client owner/asset IDs.

    On ledger failure the stored object may be orphaned. Return no success or URL,
    and do not delete/retry/fall back to a second provider automatically.
    """
    if not ledger_enabled():
        return jsonify(payload)
    if provider == 'local' and payload['url'].startswith('/'):
        payload = {**payload, 'url': urljoin(request.host_url, payload['url'])}
    db = None
    try:
        db = get_db()
        if not namespace or not isinstance(provider_id, str) or not provider_id:
            raise ValueError('Missing storage identity')
        lock_upload_owner(db, owner_id)
        asset_id = uuid.uuid4().hex
        db.execute(
            'INSERT INTO media_assets (id, owner_id, provider, storage_namespace, resource_type, provider_id, delivery_url, source_bytes) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING id',
            (asset_id, owner_id, provider, namespace, kind, provider_id, payload['url'], source_bytes),
        ).fetchone()
        consume_reservation(db, owner_id, kind, source_bytes)
        db.commit()
    except Exception:
        _rollback(db)
        current_app.logger.error('upload.registration_failed')
        return ledger_unavailable()
    return jsonify({**payload, 'assetId': asset_id})


def bind_listing_assets(media, owner_id, existing=None):
    """Validate ownership and persist verified IDs in the existing gallery column.

    Existing URL-only references are grandfathered only on that same listing.
    No cloud deletion, exclusive association or ownership inference is performed.
    """
    if not ledger_enabled() or not media:
        return media
    old = dict(existing) if existing is not None else {}
    def saved_array(key):
        value = old.get(key) or []
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except ValueError:
                return []
        return value if isinstance(value, list) else []
    old_gallery = saved_array('media_gallery')
    legacy = {('image', url) for url in saved_array('gallery_images') if isinstance(url, str)}
    for kind, key in (('image', 'image_url'), ('video', 'video_url')):
        if old.get(key):
            legacy.add((kind, old[key]))
    for item in old_gallery:
        if isinstance(item, dict) and isinstance(item.get('url'), str):
            legacy.add((item.get('type'), item['url']))
            if isinstance(item.get('thumbnail'), str):
                legacy.add(('image', item['thumbnail']))

    db = get_db()
    verified = {}
    def verify(kind, url, asset_id=None):
        if not url:
            return None
        if asset_id:
            row = db.execute('SELECT id, resource_type, delivery_url FROM media_assets WHERE id = ? AND owner_id = ?',
                             (asset_id, owner_id)).fetchone()
        else:
            row = db.execute('SELECT id, resource_type, delivery_url FROM media_assets WHERE delivery_url = ? AND owner_id = ? AND resource_type = ?',
                             (url, owner_id, kind)).fetchone()
        if row is not None and row['resource_type'] == kind and row['delivery_url'] == url:
            verified[(kind, url)] = row['id']
            return row['id']
        if not asset_id and (kind, url) in legacy:
            return None
        raise InvalidListingMedia('New media must be an upload owned by your account with matching URL and type')

    gallery = [dict(item) for item in media.get('mediaGallery', old_gallery) if isinstance(item, dict)]
    for item in gallery:
        asset_id = verify(item['type'], item['url'], item.get('assetId'))
        if asset_id:
            item['assetId'] = asset_id
        if item.get('thumbnail'):
            verify('image', item['thumbnail'])
    for key, kind in (('image', 'image'), ('videoUrl', 'video')):
        if key in media:
            verify(kind, media[key])
    for url in media.get('galleryImages', []):
        verify('image', url)
    present = {(item['type'], item['url']) for item in gallery}
    for (kind, url), asset_id in verified.items():
        if (kind, url) not in present:
            gallery.append({'type': kind, 'url': url, 'assetId': asset_id})
    result = {**media, 'mediaGallery': gallery}
    return validate_listing_media(result, existing)
