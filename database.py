
import sqlite3

DB_NAME = "medicine_inventory.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_name TEXT NOT NULL,
            category TEXT,
            manufacturer TEXT,
            minimum_stock INTEGER DEFAULT 10
        )
    """)

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
