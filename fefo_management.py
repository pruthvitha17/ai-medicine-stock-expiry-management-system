
import sqlite3
import pandas as pd

DB_NAME = "medicine_inventory.db"


def get_fefo_batches():

    conn = sqlite3.connect(DB_NAME)

    df = pd.read_sql_query("""
        SELECT
            m.medicine_name,
            b.batch_number,
            b.quantity,
            b.expiry_date
        FROM batches b
        JOIN medicines m
            ON b.medicine_id = m.id
        WHERE b.quantity > 0
        ORDER BY b.expiry_date ASC
    """, conn)

    conn.close()

    return df


if __name__ == "__main__":

    print("FEFO MANAGEMENT REPORT")
    print("-" * 60)

    results = get_fefo_batches()

    if results.empty:
        print("No available medicine batches found.")
    else:
        print(results.to_string(index=False))

    print("-" * 60)
    print("Total batches arranged:", len(results))
