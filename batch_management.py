

import sqlite3
from datetime import date, timedelta

DB_NAME = "medicine_inventory.db"


def add_batches_for_all_medicines():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT m.id, m.medicine_name, m.minimum_stock
        FROM medicines m
        WHERE NOT EXISTS (
            SELECT 1 FROM batches b
            WHERE b.medicine_id = m.id
        )
    """)

    medicines = cursor.fetchall()
    today = date.today()

    added = 0

    for medicine_id, name, minimum_stock in medicines:

        quantity = minimum_stock + 20

        # Sample expiry dates to demonstrate different risk levels
        days = [15, 60, 150, -10][medicine_id % 4]

        manufacturing_date = today - timedelta(days=180)
        expiry_date = today + timedelta(days=days)

        batch_number = f"DEMO-{medicine_id:03d}"

        cursor.execute("""
            INSERT INTO batches
            (medicine_id, batch_number, quantity,
             manufacturing_date, expiry_date,
             purchase_price, selling_price)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            medicine_id,
            batch_number,
            quantity,
            manufacturing_date.isoformat(),
            expiry_date.isoformat(),
            0.0,
            0.0
        ))

        added += 1

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM medicines")
    total_medicines = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT medicine_id) FROM batches")
    medicines_with_batches = cursor.fetchone()[0]

    conn.close()

    print("Sample batches added:", added)
    print("Total medicines:", total_medicines)
    print("Medicines with batches:", medicines_with_batches)


if __name__ == "__main__":
    add_batches_for_all_medicines()
