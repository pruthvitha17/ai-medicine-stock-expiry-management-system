
import sqlite3

DB_NAME = "medicine_inventory.db"


def check_low_stock():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT m.medicine_name,
               m.minimum_stock,
               COALESCE(SUM(b.quantity), 0)
        FROM medicines m
        LEFT JOIN batches b ON m.id = b.medicine_id
        GROUP BY m.id
        ORDER BY m.medicine_name
    """)

    records = cursor.fetchall()
    conn.close()

    results = []

    for medicine, minimum, quantity in records:

        if quantity <= minimum:
            status = "Low Stock"
        else:
            status = "Sufficient Stock"

        results.append((
            medicine,
            quantity,
            minimum,
            status
        ))

    return results


if __name__ == "__main__":

    print("MEDICINE STOCK REPORT")
    print("-" * 60)

    for item in check_low_stock():
        print(item)

    print("-" * 60)
    print("Total medicines:", len(check_low_stock()))
