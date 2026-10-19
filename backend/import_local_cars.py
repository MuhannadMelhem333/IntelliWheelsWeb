"""Import the bundled JSON into the existing local preview SQLite database only.

Run from the repository root: .venv/Scripts/python backend/import_local_cars.py
Refuses a nonempty cars table, and never reads DATABASE_URL or connects remotely.
"""
import json
import sqlite3
from contextlib import closing
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    records = json.loads((root / "data" / "cars.json").read_text(encoding="utf-8"))
    database = root / "intelliwheels.db"
    if not database.is_file():
        raise SystemExit("Start the local backend first to initialize its schema.")
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        if connection.execute("SELECT COUNT(*) FROM cars").fetchone()[0]:
            raise SystemExit("Import skipped: cars table is not empty. No rows changed.")
        for car in records:
            # Legacy string IDs cannot be used by the integer-ID API. SQLite
            # assigns new IDs; retain the source identifier for traceability.
            images = car.get("imageUrls", [])
            connection.execute(
                """INSERT INTO cars
                (make, model, year, price, currency, image_url, image_urls,
                 gallery_images, rating, reviews, specs, source_sheets)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (car["make"], car["model"], car.get("year"), car.get("price"),
                 car.get("currency", "JOD"), car.get("image"), json.dumps(images),
                 json.dumps(images), car.get("rating"), car.get("reviews", 0),
                 json.dumps(car.get("specs", {})), json.dumps([car.get("id")])),
            )
    print(f"Imported {len(records)} cars into local preview SQLite. Source JSON unchanged.")


if __name__ == "__main__":
    main()
