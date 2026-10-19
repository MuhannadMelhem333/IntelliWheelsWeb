"""Explicit SQLite-only additive migration. Does not import the Flask app or .env.

Default is read-only inspection. --apply requires a new backup destination.
Hosted database migrations require a separate reviewed staging rollout.
"""
import argparse
from contextlib import closing
from pathlib import Path
import sqlite3


def migrate(database, backup=None, migration='ledger'):
    choices = {'ledger': ('media_assets', '001_media_assets.sql'),
               'quotas': ('upload_reservations', '002_upload_reservations.sql'),
               'signed': ('signed_upload_intents', '003_signed_upload_intents.sql')}
    if migration not in choices:
        raise ValueError('Unknown migration')
    table, filename = choices[migration]
    database = Path(database).resolve(strict=True)
    if not database.is_file():
        raise ValueError('Database must be an existing file')
    with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as source:
        if not source.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'").fetchone():
            raise ValueError('Expected application users table is missing')
        if migration == 'quotas' and not source.execute("SELECT name FROM sqlite_master WHERE name='media_assets'").fetchone():
            raise ValueError('Apply the ledger migration first')
        if migration == 'signed' and not source.execute("SELECT name FROM sqlite_master WHERE name='upload_reservations'").fetchone():
            raise ValueError('Apply the quota migration first')
        applied = source.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None
        if backup is None:
            if migration == 'signed':
                return 'Signed upload table present' if applied else 'Signed upload migration pending'
            return ('Media ledger table present' if applied else 'Media ledger migration pending') if migration == 'ledger' else ('Upload quota table present' if applied else 'Upload quota migration pending')
        backup = Path(backup).resolve()
        # Exclusive creation refuses existing files, symlinks and the source path.
        with backup.open('xb'):
            pass
        with closing(sqlite3.connect(backup)) as destination:
            source.backup(destination)
    sql = (Path(__file__).parent / 'migrations' / filename).read_text(encoding='utf-8')
    with closing(sqlite3.connect(database.as_uri() + '?mode=rw', uri=True)) as connection:
        connection.execute('PRAGMA foreign_keys = ON')
        connection.executescript('BEGIN IMMEDIATE;\n' + sql + '\nCOMMIT;')
    return 'Upload migration applied; backup retained'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--backup')
    parser.add_argument('--migration', choices=['ledger', 'quotas', 'signed'], default='ledger')
    args = parser.parse_args()
    if args.apply != bool(args.backup):
        parser.error('--apply and a new --backup path must be supplied together')
    try:
        print(migrate(args.database, args.backup, args.migration))
    except Exception:
        parser.exit(1, 'Migration failed; check the database and backup paths. No rollback was attempted.\n')
