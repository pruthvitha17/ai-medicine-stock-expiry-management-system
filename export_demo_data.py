
import sqlite3
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "medicine_inventory.db"
DATA_DIR = BASE_DIR / "dataset"

DATA_DIR.mkdir(exist_ok=True)

conn = sqlite3.connect(DB_PATH)

tables = ["medicines", "batches", "sales"]

for table in tables:
    cursor = conn.execute(f"SELECT * FROM {table}")
    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()

    output_file = DATA_DIR / f"seed_{table}.csv"

    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows(rows)

    print(f"{table}: {len(rows)} records exported")

conn.close()

print("Demo data export completed!")
