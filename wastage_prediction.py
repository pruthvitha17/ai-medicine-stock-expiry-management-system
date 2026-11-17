
import sqlite3
from datetime import date, datetime

DB_NAME = "medicine_inventory.db"


def predict_wastage():

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

    records = cursor.fetchall()
    conn.close()

    wastage_report = []

    today = date.today()

    for medicine, batch, quantity, expiry in records:

        if expiry is None:
            wastage_report.append({
                "medicine": medicine,
                "batch": "No Batch",
                "quantity": 0,
                "days_left": "Not Available",
                "risk": "Batch Not Added"
            })
            continue

        expiry_date = datetime.strptime(
            expiry, "%Y-%m-%d"
        ).date()

        days_left = (expiry_date - today).days

        if days_left < 0:
            risk = "Expired Stock"
        elif days_left <= 30:
            risk = "High Wastage Risk"
        elif days_left <= 90:
            risk = "Medium Wastage Risk"
        else:
            risk = "Low Wastage Risk"

        wastage_report.append({
            "medicine": medicine,
            "batch": batch,
            "quantity": quantity,
            "days_left": days_left,
            "risk": risk
        })

    return wastage_report


if __name__ == "__main__":

    print("MEDICINE WASTAGE REPORT")
    print("-" * 60)

    results = predict_wastage()

    for item in results:
        print(item)

    print("-" * 60)
    print("Total medicines checked:", len(results))
