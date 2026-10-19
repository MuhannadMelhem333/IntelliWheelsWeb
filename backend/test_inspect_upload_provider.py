from contextlib import closing
import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock

from inspect_upload_provider import load_intents, observe, reconcile


def intent():
    return {'id': 'a' * 32, 'public_id': 'intelliwheels/staging/image/' + 'a' * 32,
            'resource_type': 'image', 'asset_id': 'ledger', 'provider_asset_id': 'original',
            'provider_version': 1, 'max_bytes': 100}


def asset(kind='image', **overrides):
    return {'asset_id': 'original', 'resource_type': kind, 'type': 'upload',
            'public_id': intent()['public_id'], 'version': 1, 'bytes': 50, **overrides}


class ProviderInventoryTest(unittest.TestCase):
    def test_all_resource_types_scanned_and_cross_type_bytes_counted(self):
        def fetch(**options):
            self.assertEqual(options['prefix'], intent()['public_id'])
            self.assertEqual(options['type'], 'upload')
            kind = options['resource_type']
            return {'resources': [asset(kind, asset_id=kind)]}
        report = reconcile([intent()], fetch)
        self.assertEqual(report['observed_assets'], 3)
        self.assertEqual(report['observed_bytes'], 150)
        self.assertEqual(report['unexpected_resource_type'], 2)
        self.assertEqual(report['completed_identity_mismatch'], 1)
        self.assertFalse(report['automatic_refunds_allowed'])
        self.assertFalse(report['automatic_deletions_allowed'])
        self.assertNotIn(intent()['public_id'], str(report))

    def test_raw_extension_variants_are_visible_not_silently_discarded(self):
        report = observe(intent(), lambda **options: {'resources': [asset('raw', public_id=intent()['public_id'] + '.zip')]} if options['resource_type'] == 'raw' else {'resources': []})
        self.assertEqual(report['unexpected_public_id'], 1)
        self.assertEqual(report['unexpected_resource_type'], 1)
        self.assertFalse(report['expected_object_seen'])

    def test_pagination_is_bounded_and_partial_is_explicit(self):
        fetch = Mock(return_value={'resources': [], 'next_cursor': 'more'})
        report = observe(intent(), fetch, max_pages=1)
        self.assertEqual(fetch.call_count, 3)
        self.assertFalse(report['complete_listing'])

    def test_pagination_follows_cursor_and_detects_repeated_assets(self):
        def fetch(**options):
            if options['resource_type'] != 'image':
                return {'resources': []}
            if 'next_cursor' in options:
                self.assertEqual(options['next_cursor'], 'next')
                return {'resources': [asset()]}
            return {'resources': [asset()], 'next_cursor': 'next'}
        report = observe(intent(), fetch)
        self.assertEqual(report['observed_assets'], 1)
        self.assertFalse(report['complete_listing'])

    def test_provider_errors_and_malformed_responses_are_unknown_not_absent(self):
        for response in (None, {}, {'resources': 'invalid'}, {'resources': [asset(bytes=True)]},
                         {'resources': [asset(public_id='outside-scope')]}):
            with self.subTest(response=response):
                self.assertFalse(observe(intent(), Mock(return_value=response))['complete_listing'])
        report = reconcile([intent()], Mock(side_effect=RuntimeError('private-secret')))
        self.assertEqual(report['incomplete_intents'], 1)
        self.assertNotIn('private-secret', str(report))

    def test_valid_completion_and_missing_object_are_distinct(self):
        fetch = lambda **options: {'resources': [asset()]} if options['resource_type'] == 'image' else {'resources': []}
        report = observe(intent(), fetch)
        self.assertTrue(report['complete_listing'])
        self.assertTrue(report['expected_object_seen'])
        self.assertEqual(report['completed_identity_mismatch'], 0)
        missing = reconcile([intent()], lambda **options: {'resources': []})
        self.assertEqual(missing['expected_object_not_seen'], 1)
        self.assertFalse(missing['automatic_refunds_allowed'])

    def test_scope_load_is_read_only_filtered_and_bounded(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'fixture.db'
            with closing(sqlite3.connect(path)) as db:
                db.execute('CREATE TABLE users (id INTEGER PRIMARY KEY)')
                for migration in sorted((Path(__file__).parent / 'migrations').glob('*.sql')):
                    db.executescript(migration.read_text())
                for index, environment in enumerate(('staging', 'staging', 'production')):
                    identity = f'{index:032x}'
                    db.execute('INSERT INTO signed_upload_intents (id, owner_id, request_key, resource_type, public_id, cloud_name, preset, environment, max_bytes, issued_at) VALUES (?,1,?,\'image\',?,\'fixture-cloud\',\'preset\',?,100,1000)',
                               (identity, identity, f'intelliwheels/{environment}/image/{identity}', environment))
                db.commit()
            before = hashlib.sha256(path.read_bytes()).digest()
            rows, truncated = load_intents(path, 'fixture-cloud', 'staging', 1)
            self.assertEqual(len(rows), 1)
            self.assertTrue(truncated)
            self.assertEqual(before, hashlib.sha256(path.read_bytes()).digest())
            self.assertEqual(load_intents(path, 'different-cloud', 'staging', 1), ([], False))
            with closing(sqlite3.connect(path)) as db:
                db.execute("UPDATE signed_upload_intents SET public_id='outside-scope' WHERE id=?", (f'{0:032x}',))
                db.commit()
            with self.assertRaises(ValueError):
                load_intents(path, 'fixture-cloud', 'staging', 1)

    def test_invalid_page_bound_and_scope_truncation(self):
        fetch = Mock()
        with self.assertRaises(ValueError):
            observe(intent(), fetch, max_pages=6)
        fetch.assert_not_called()
        self.assertTrue(reconcile([], fetch, truncated=True)['scope_truncated'])


if __name__ == '__main__':
    unittest.main()
