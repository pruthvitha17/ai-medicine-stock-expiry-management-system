
import sqlite3
from datetime import date, datetime

DB_NAME = "medicine_inventory.db"


def check_expiry():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT m.medicine_name,
               b.batch_number,
               b.quantity,
               b.expiry_date
        FROM medicines m
        LEFT JOIN batches b ON m.id = b.medicine_id
        ORDER BY m.medicine_name
    """)

    batches = cursor.fetchall()
    conn.close()

    results = []

    today = date.today()

    for batch in batches:

        medicine, batch_no, quantity, expiry = batch

        if expiry is None:
            results.append((
                medicine,
                "No Batch",
                0,
                "Not Available",
                "Not Available",
                "Batch Not Added"
            ))
            continue

        expiry_date = datetime.strptime(
            expiry, "%Y-%m-%d"
        ).date()

        days_left = (expiry_date - today).days

        if days_left < 0:
            status = "Expired"
        elif days_left <= 30:
            status = "High Risk"
        elif days_left <= 90:
            status = "Medium Risk"
        else:
            status = "Safe"

        results.append((
            medicine,
            batch_no,
            quantity,
            expiry,
            days_left,
            status
        ))

    return results


if __name__ == "__main__":

    print("MEDICINE EXPIRY REPORT")
    print("-" * 70)

    for item in check_expiry():
        print(item)

    print("-" * 70)
    print("Total medicine records:", len(check_expiry()))
