
import sqlite3
from pathlib import Path

# Project folder
BASE_DIR = Path(__file__).resolve().parent

# Database location
DB_NAME = BASE_DIR / "medicine_inventory.db"


def get_connection():
    conn = sqlite3.connect(str(DB_NAME))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


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


if __name__ == "__main__":
    create_tables()
    print("Database and tables created successfully!")
