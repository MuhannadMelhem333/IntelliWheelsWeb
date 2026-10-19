import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest

from inspect_uploads import inspect


class UploadInventoryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'fixture.db'
        self.db = sqlite3.connect(self.path)
        self.addCleanup(self.db.close)
        self.db.executescript('CREATE TABLE users (id INTEGER PRIMARY KEY); INSERT INTO users VALUES (1);')
        for name in ('001_media_assets.sql', '002_upload_reservations.sql'):
            self.db.executescript((Path(__file__).parent / 'migrations' / name).read_text())

    def signed(self):
        self.db.executescript((Path(__file__).parent / 'migrations/003_signed_upload_intents.sql').read_text())

    def intent(self, name='fixture', issued=1000):
        self.db.execute('INSERT INTO signed_upload_intents (id, owner_id, request_key, resource_type, public_id, cloud_name, preset, environment, max_bytes, issued_at) VALUES (?, 1, ?, ?, ?, ?, ?, ?, 100, ?)',
                        (name, name, 'image', 'private-public-id-' + name, 'private-cloud', 'preset', 'development', issued))
        self.db.execute("INSERT INTO upload_reservations (id, owner_id, resource_type, source_bytes) VALUES (?, 1, 'image', 100)", (name,))
        self.db.commit()

    def test_missing_signed_schema_is_reported_without_creation(self):
        report = inspect(self.path, now=5000)
        self.assertFalse(report['signed_schema_present'])
        self.assertFalse(report['provider_checked'])
        self.assertIsNone(self.db.execute("SELECT name FROM sqlite_master WHERE name='signed_upload_intents'").fetchone())

    def test_expiry_does_not_authorize_refund_or_change_database(self):
        self.signed()
        self.intent()
        before = hashlib.sha256(self.path.read_bytes()).digest()
        report = inspect(self.path, now=4600)
        self.assertEqual(report['signed']['expired_pending'], 1)
        self.assertEqual(report['signed']['inconsistent'], 0)
        self.assertFalse(report['automatic_refunds_allowed'])
        self.assertFalse(report['automatic_deletions_allowed'])
        self.assertEqual(before, hashlib.sha256(self.path.read_bytes()).digest())
        self.assertNotIn('private', str(report))

    def test_completed_signature_still_active_and_mismatches_detected(self):
        self.signed()
        self.intent()
        self.db.execute("INSERT INTO media_assets VALUES ('asset', 1, 'cloudinary', 'private-cloud', 'image', 'private-public-id-fixture', 'private-url', 50, CURRENT_TIMESTAMP)")
        self.db.execute("UPDATE signed_upload_intents SET asset_id='asset', provider_asset_id='immutable', provider_version=1")
        self.db.commit()
        report = inspect(self.path, now=1100)
        self.assertEqual(report['signed']['completed'], 1)
        self.assertEqual(report['signed']['active_completed'], 1)
        self.assertEqual(report['signed']['inconsistent'], 0)
        self.db.execute("UPDATE media_assets SET provider_id='different'")
        self.db.commit()
        self.assertEqual(inspect(self.path, now=1100)['signed']['inconsistent'], 1)

    def test_missing_reservation_and_future_timestamp_fail_consistency(self):
        self.signed()
        self.intent()
        self.intent('future', 99999)
        self.db.execute("DELETE FROM upload_reservations WHERE id='fixture'")
        self.db.commit()
        self.assertEqual(inspect(self.path, now=5000)['signed']['inconsistent'], 2)

    def test_proxy_reservations_are_unmatched_not_refundable(self):
        self.signed()
        self.db.execute("INSERT INTO upload_reservations (id,owner_id,resource_type,source_bytes) VALUES ('proxy',1,'video',200)")
        self.db.commit()
        report = inspect(self.path, now=5000)
        self.assertEqual(report['unmatched_reservations'], 1)
        self.assertEqual(report['reservations']['source_bytes'], 200)
        self.assertFalse(report['automatic_refunds_allowed'])

    def test_missing_database_is_not_created(self):
        missing = self.path.parent / 'missing.db'
        with self.assertRaises(FileNotFoundError):
            inspect(missing)
        self.assertFalse(missing.exists())


if __name__ == '__main__':
    unittest.main()
