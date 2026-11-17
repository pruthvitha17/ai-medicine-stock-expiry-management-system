
import sqlite3
import csv
from pathlib import Path

# ---------------- PROJECT PATHS ----------------

BASE_DIR = Path(__file__).resolve().parent

DB_NAME = BASE_DIR / "medicine_inventory.db"

DATASET_DIR = BASE_DIR / "dataset"


# ---------------- DATABASE CONNECTION ----------------

def get_connection():
    conn = sqlite3.connect(str(DB_NAME))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------- CREATE DATABASE TABLES ----------------

def create_tables():

    conn = get_connection()
    cursor = conn.cursor()

    # Medicines table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_name TEXT NOT NULL,
            category TEXT,
            manufacturer TEXT,
            minimum_stock INTEGER DEFAULT 10
        )
    """)

    # Batches table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_id INTEGER,
            batch_number TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            manufacturing_date TEXT,
            expiry_date TEXT NOT NULL,
            purchase_price REAL DEFAULT 0,
            selling_price REAL DEFAULT 0,
            FOREIGN KEY (medicine_id) REFERENCES medicines(id)
        )
    """)

    # Sales table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_id INTEGER,
            quantity_sold INTEGER NOT NULL,
            sale_date TEXT NOT NULL,
            FOREIGN KEY (medicine_id) REFERENCES medicines(id)
        )
    """)

    conn.commit()
    conn.close()


# ---------------- LOAD DEMO DATA ----------------

def seed_demo_data():

    conn = get_connection()
    cursor = conn.cursor()

    try:

        # Check whether medicine records already exist
        count = cursor.execute(
            "SELECT COUNT(*) FROM medicines"
        ).fetchone()[0]

        # Insert demo data only into an empty database
        if count == 0:

            tables = [
                "medicines",
                "batches",
                "sales"
            ]

            for table in tables:

                csv_path = DATASET_DIR / f"seed_{table}.csv"

                if not csv_path.exists():
                    raise FileNotFoundError(
                        f"Demo data file not found: {csv_path}"
                    )

                with open(
                    csv_path,
                    "r",
                    encoding="utf-8-sig",
                    newline=""
                ) as file:

                    reader = csv.DictReader(file)

                    columns = reader.fieldnames

                    if not columns:
                        raise ValueError(
                            f"CSV file has no headers: {csv_path}"
                        )

                    rows = list(reader)

                    if rows:

                        column_names = ", ".join(columns)

                        placeholders = ", ".join(
                            ["?"] * len(columns)
                        )

                        query = (
                            f"INSERT INTO {table} "
                            f"({column_names}) "
                            f"VALUES ({placeholders})"
                        )

                        values = [
                            tuple(row[column] for column in columns)
                            for row in rows
                        ]

                        cursor.executemany(query, values)

                        print(
                            f"{table}: {len(rows)} records loaded"
                        )

            conn.commit()

            print("Demo data loaded successfully!")

        else:

            print("Database already contains medicine records.")
            print("Demo data was not inserted again.")

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# ---------------- MAIN ----------------

if __name__ == "__main__":

    create_tables()

    seed_demo_data()

    print("Database setup completed successfully!")
