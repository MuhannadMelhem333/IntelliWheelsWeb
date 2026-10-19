"""Conservative per-account source-byte/count budgets, including in-flight uploads.

Not Cloudinary billable storage accounting. Never expire an ambiguous reservation
without reconciling whether a provider object exists.
"""
import uuid
from flask import current_app, g, jsonify
from .db import get_db, is_postgres


def lock_upload_owner(db, owner_id):
    if not current_app.config['UPLOAD_QUOTAS_ENABLED']:
        return
    if is_postgres():
        db.execute('SELECT id FROM users WHERE id = ? FOR UPDATE', (owner_id,)).fetchone()
    else:
        db.execute('BEGIN IMMEDIATE')


def reserve_upload(owner_id, kind, source_bytes, *, commit=True):
    if not current_app.config['UPLOAD_QUOTAS_ENABLED']:
        return None
    db = get_db()
    try:
        if not current_app.config['MEDIA_ASSET_LEDGER_ENABLED']:
            raise ValueError('Quota requires ledger')
        # Serialize budget checks across workers, not just Python threads.
        lock_upload_owner(db, owner_id)
        used = db.execute('SELECT COUNT(*) AS count, COALESCE(SUM(source_bytes), 0) AS bytes FROM media_assets WHERE owner_id = ?', (owner_id,)).fetchone()
        pending = db.execute('SELECT COUNT(*) AS count, COALESCE(SUM(source_bytes), 0) AS bytes FROM upload_reservations WHERE owner_id = ?', (owner_id,)).fetchone()
        if (used['count'] + pending['count'] + 1 > current_app.config['UPLOAD_USER_MAX_ASSETS'] or
                used['bytes'] + pending['bytes'] + source_bytes > current_app.config['UPLOAD_USER_MAX_BYTES']):
            db.rollback()
            response = jsonify({'success': False, 'error': 'Upload allowance exceeded. Contact support.', 'code': 'upload_quota_exceeded'})
            response.status_code = 409
            response.headers['Cache-Control'] = 'no-store'
            return response
        reservation_id = uuid.uuid4().hex
        db.execute('INSERT INTO upload_reservations (id, owner_id, resource_type, source_bytes) VALUES (?, ?, ?, ?) RETURNING id',
                   (reservation_id, owner_id, kind, source_bytes)).fetchone()
        if commit:
            db.commit()
        g.upload_reservation_id = reservation_id
        return None
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        current_app.logger.error('upload.quota_unavailable')
        response = jsonify({'success': False, 'error': 'Upload allowance is temporarily unavailable.'})
        response.status_code = 503
        response.headers['Cache-Control'] = 'no-store'
        return response


def consume_reservation(db, owner_id, kind, source_bytes):
    """Move reserved usage into ledger usage in the ledger insert transaction."""
    if not current_app.config['UPLOAD_QUOTAS_ENABLED']:
        return
    reservation_id = getattr(g, 'upload_reservation_id', None)
    row = db.execute('SELECT id, source_bytes FROM upload_reservations WHERE id = ? AND owner_id = ? AND resource_type = ?',
                     (reservation_id, owner_id, kind)).fetchone()
    if row is None or not 0 < source_bytes <= row['source_bytes']:
        raise ValueError('Matching upload reservation required')
    db.execute('DELETE FROM upload_reservations WHERE id = ?', (reservation_id,))
