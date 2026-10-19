"""Standard-library tests; temporary SQLite files only, no running backend needed."""
import contextlib
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import import_local_cars


class LocalCarImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'data').mkdir()
        self.source = self.root / 'data' / 'cars.json'
        self.car = {'id': 'original-slug', 'make': 'Toyota', 'model': 'Camry',
                    'imageUrls': ['https://example.test/car.jpg'], 'specs': {'bodyStyle': 'Sedan'}}
        self.source.write_text(json.dumps([self.car]), encoding='utf-8')
        self.database = self.root / 'intelliwheels.db'
        with contextlib.closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute('''CREATE TABLE cars (id INTEGER PRIMARY KEY,
                make TEXT NOT NULL, model TEXT NOT NULL, year INTEGER, price REAL,
                currency TEXT, image_url TEXT, image_urls TEXT, gallery_images TEXT,
                rating REAL, reviews INTEGER, specs TEXT, source_sheets TEXT)''')
        self.patcher = patch.object(import_local_cars, '__file__', str(self.root / 'import_local_cars.py'))
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def run_import(self):
        with contextlib.redirect_stdout(io.StringIO()):
            import_local_cars.main()

    def count(self):
        with contextlib.closing(sqlite3.connect(self.database)) as connection:
            return connection.execute('SELECT COUNT(*) FROM cars').fetchone()[0]

    def test_import_preserves_source_and_maps_ids_and_gallery(self):
        original = self.source.read_bytes()
        self.run_import()
        self.assertEqual(self.source.read_bytes(), original)
        with contextlib.closing(sqlite3.connect(self.database)) as connection:
            row = connection.execute('SELECT id, gallery_images, source_sheets FROM cars').fetchone()
        self.assertEqual(row[0], 1)
        self.assertEqual(json.loads(row[1]), self.car['imageUrls'])
        self.assertEqual(json.loads(row[2]), ['original-slug'])

    def test_repeat_import_refuses_to_change_existing_rows(self):
        self.run_import()
        with self.assertRaises(SystemExit):
            self.run_import()
        self.assertEqual(self.count(), 1)

    def test_bad_record_rolls_back_entire_import(self):
        self.source.write_text(json.dumps([self.car, {'make': 'Missing model'}]), encoding='utf-8')
        with self.assertRaises(KeyError):
            self.run_import()
        self.assertEqual(self.count(), 0)

    def test_missing_database_is_not_created(self):
        self.database.unlink()
        with self.assertRaises(SystemExit):
            self.run_import()
        self.assertFalse(self.database.exists())


if __name__ == '__main__':
    unittest.main()
