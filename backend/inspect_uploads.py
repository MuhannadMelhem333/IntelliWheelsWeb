"""Read-only SQLite upload reconciliation inventory; no Flask or provider imports.

Counts are diagnostic, never authorization to refund quota or delete assets.
No credentials, delivery URLs, public IDs, or account identifiers are emitted.
"""
import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import time


def inspect(database, now=None):
    database = Path(database).resolve(strict=True)
    if not database.is_file():
        raise ValueError('Existing SQLite database required')
    now = int(time.time()) if now is None else now
    with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as db:
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA query_only = ON')
        db.execute('BEGIN')  # A consistent snapshot, including optional table discovery.
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'users', 'media_assets', 'upload_reservations'} <= tables:
            raise ValueError('Ledger and quota migrations required')
        assets = db.execute('SELECT COUNT(*), COALESCE(SUM(source_bytes), 0) FROM media_assets').fetchone()
        reservations = db.execute('SELECT COUNT(*), COALESCE(SUM(source_bytes), 0) FROM upload_reservations').fetchone()
        report = {
            'read_only': True,
            'ledger': {'assets': assets[0], 'source_bytes': assets[1]},
            'reservations': {'count': reservations[0], 'source_bytes': reservations[1]},
            'signed_schema_present': 'signed_upload_intents' in tables,
            'signed': {'pending': 0, 'expired_pending': 0, 'completed': 0,
                       'active_completed': 0, 'inconsistent': 0},
            'unmatched_reservations': reservations[0],
            'provider_checked': False,
            'automatic_refunds_allowed': False,
            'automatic_deletions_allowed': False,
        }
        if not report['signed_schema_present']:
            return report
        report['unmatched_reservations'] = db.execute('''
            SELECT COUNT(*) FROM upload_reservations r
            WHERE NOT EXISTS (SELECT 1 FROM signed_upload_intents i WHERE i.id = r.id)
        ''').fetchone()[0]
        # Stream a left join rather than loading private asset/account records into a report.
        rows = db.execute('''
            SELECT i.owner_id, i.resource_type, i.max_bytes, i.issued_at,
                   i.asset_id, i.public_id, i.cloud_name, i.provider_asset_id, i.provider_version,
                   r.id AS reservation_id, r.owner_id AS reservation_owner,
                   r.resource_type AS reservation_kind, r.source_bytes AS reserved_bytes,
                   a.id AS ledger_id, a.owner_id AS ledger_owner,
                   a.resource_type AS ledger_kind, a.provider, a.storage_namespace,
                   a.provider_id, a.source_bytes AS ledger_bytes
            FROM signed_upload_intents i
            LEFT JOIN upload_reservations r ON r.id = i.id
            LEFT JOIN media_assets a ON a.id = i.asset_id
        ''')
        for row in rows:
            pending = row['asset_id'] is None
            issued = row['issued_at']
            valid_time = type(issued) is int and 0 <= issued <= now
            expired = valid_time and now - issued >= 3600
            stats = report['signed']
            stats['pending' if pending else 'completed'] += 1
            if pending and expired:
                stats['expired_pending'] += 1
            if not pending and valid_time and not expired:
                stats['active_completed'] += 1
            held = (row['reservation_id'] is not None and
                              row['reservation_owner'] == row['owner_id'] and
                              row['reservation_kind'] == row['resource_type'] and
                              row['reserved_bytes'] == row['max_bytes'])
            if pending:
                consistent = held
            else:
                consistent = (held and row['ledger_id'] is not None and
                              row['ledger_owner'] == row['owner_id'] and
                              row['ledger_kind'] == row['resource_type'] and
                              row['provider'] == 'cloudinary' and
                              row['storage_namespace'] == row['cloud_name'] and
                              row['provider_id'] == row['public_id'] and
                              0 < row['ledger_bytes'] <= row['max_bytes'] and
                              bool(row['provider_asset_id']) and
                              type(row['provider_version']) is int and row['provider_version'] > 0)
            if not consistent or not valid_time or row['max_bytes'] <= 0:
                stats['inconsistent'] += 1
        return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(inspect(args.database), indent=2, sort_keys=True))
    except Exception:
        parser.exit(1, 'Upload inspection failed. Check the database path and migration schema.\n')
