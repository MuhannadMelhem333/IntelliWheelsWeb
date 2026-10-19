"""Bounded, read-only Cloudinary observations for locally recorded signed intents.

No automatic refund, deletion, upload, signature generation or database mutation.
Credentials must already be in the process environment; .env is never loaded.
"""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import re
import sqlite3


def load_intents(database, cloud_name, environment, limit):
    if environment not in ('development', 'staging', 'production') or not 1 <= limit <= 25:
        raise ValueError('Invalid scope or limit')
    path = Path(database).resolve(strict=True)
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as db:
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA query_only=ON')
        db.execute('BEGIN')
        rows = db.execute('''SELECT id, public_id, resource_type, provider_asset_id, provider_version,
                            asset_id, max_bytes FROM signed_upload_intents
                            WHERE cloud_name=? AND environment=? ORDER BY issued_at, id LIMIT ?''',
                          (cloud_name, environment, limit + 1)).fetchall()
        truncated = len(rows) > limit
        intents = [dict(row) for row in rows[:limit]]
    # Validate every row before allowing any provider call.
    for row in intents:
        if (not re.fullmatch(r'[0-9a-f]{32}', row['id']) or row['resource_type'] not in ('image', 'video') or
                row['public_id'] != f"intelliwheels/{environment}/{row['resource_type']}/{row['id']}"):
            raise ValueError('Intent namespace mismatch')
    return intents, truncated


def observe(intent, fetch_page, max_pages=2):
    """Counts are observed lower bounds, not a storage bill or proof of absence."""
    if not 1 <= max_pages <= 5:
        raise ValueError('Invalid page bound')
    report = {'complete_listing': True, 'observed_assets': 0, 'observed_bytes': 0,
              'unexpected_resource_type': 0, 'unexpected_public_id': 0,
              'completed_identity_mismatch': 0, 'expected_object_seen': False}
    identities = set()
    for kind in ('image', 'video', 'raw'):
        cursor = None
        cursors = set()
        for _ in range(max_pages):
            try:
                options = {'resource_type': kind, 'type': 'upload', 'prefix': intent['public_id'],
                           'max_results': 100}
                if cursor:
                    options['next_cursor'] = cursor
                page = fetch_page(**options)
                if not isinstance(page, dict) or not isinstance(page.get('resources'), list) or len(page['resources']) > 100:
                    raise ValueError('Invalid provider page')
                for asset in page['resources']:
                    if (not isinstance(asset, dict) or asset.get('resource_type') != kind or
                            asset.get('type') != 'upload' or not isinstance(asset.get('public_id'), str) or
                            not asset['public_id'].startswith(intent['public_id']) or
                            not isinstance(asset.get('asset_id'), str) or not asset['asset_id'] or
                            type(asset.get('bytes')) is not int or asset['bytes'] < 0 or
                            type(asset.get('version')) is not int or asset['version'] <= 0):
                        raise ValueError('Invalid observed metadata')
                    identity = asset['asset_id']
                    if identity in identities:
                        # Pages can move during a live scan. Never assert completeness.
                        report['complete_listing'] = False
                        continue
                    identities.add(identity)
                    report['observed_assets'] += 1
                    report['observed_bytes'] += asset['bytes']
                    if kind != intent['resource_type']:
                        report['unexpected_resource_type'] += 1
                    if asset['public_id'] != intent['public_id']:
                        report['unexpected_public_id'] += 1
                    if kind == intent['resource_type'] and asset['public_id'] == intent['public_id']:
                        report['expected_object_seen'] = True
                        if intent['asset_id'] and (identity != intent['provider_asset_id'] or asset['version'] != intent['provider_version']):
                            report['completed_identity_mismatch'] += 1
                cursor = page.get('next_cursor')
                if cursor is None or cursor == '':
                    break
                if not isinstance(cursor, str) or cursor in cursors:
                    raise ValueError('Invalid pagination cursor')
                cursors.add(cursor)
            except Exception:
                # Authentication, timeout, not-found, throttling and malformed data
                # are unknown, never evidence that provider storage is empty.
                report['complete_listing'] = False
                break
        else:
            report['complete_listing'] = False
    return report


def reconcile(intents, fetch_page, max_pages=2, truncated=False):
    report = {'read_only': True, 'scope_truncated': truncated, 'intents_observed': len(intents),
              'incomplete_intents': 0, 'observed_assets': 0, 'observed_bytes': 0,
              'unexpected_resource_type': 0, 'unexpected_public_id': 0,
              'completed_identity_mismatch': 0, 'expected_object_not_seen': 0,
              'automatic_refunds_allowed': False, 'automatic_deletions_allowed': False}
    for intent in intents:
        observed = observe(intent, fetch_page, max_pages)
        report['incomplete_intents'] += not observed['complete_listing']
        report['expected_object_not_seen'] += not observed['expected_object_seen']
        for key in ('observed_assets', 'observed_bytes', 'unexpected_resource_type',
                    'unexpected_public_id', 'completed_identity_mismatch'):
            report[key] += observed[key]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True)
    parser.add_argument('--environment', required=True, choices=['development', 'staging', 'production'])
    parser.add_argument('--limit', type=int, default=10, choices=range(1, 26))
    parser.add_argument('--max-pages', type=int, default=2, choices=range(1, 6))
    parser.add_argument('--query-provider', action='store_true', help='Explicitly permit bounded provider GET requests')
    args = parser.parse_args()
    if not args.query_provider:
        parser.error('Use inspect_uploads.py for offline inventory; provider queries require --query-provider')
    try:
        options = {key: os.environ.get(env, '') for key, env in (
            ('cloud_name', 'CLOUDINARY_CLOUD_NAME'), ('api_key', 'CLOUDINARY_API_KEY'), ('api_secret', 'CLOUDINARY_API_SECRET'))}
        if not all(options.values()) or not re.fullmatch(r'[A-Za-z0-9_-]+', options['cloud_name']):
            raise ValueError('Provider credentials missing')
        intents, truncated = load_intents(args.database, options['cloud_name'], args.environment, args.limit)
        import cloudinary.api  # Only this explicit opt-in path imports the provider.
        def fetch_page(**params):
            return cloudinary.api.resources(**params, **options, timeout=10)
        report = reconcile(intents, fetch_page, args.max_pages, truncated)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2 if report['scope_truncated'] or report['incomplete_intents'] else 0
    except Exception:
        # Never echo provider exceptions: they may contain credentials or URLs.
        parser.exit(1, 'Provider inspection failed. Check scope, credentials and database schema privately.\n')


if __name__ == '__main__':
    raise SystemExit(main())
