
import sqlite3
import pandas as pd

DB_NAME = "medicine_inventory.db"

def import_medicines():
    df = pd.read_csv("dataset/medicine_master.csv")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO medicines
            (medicine_name, category, manufacturer, minimum_stock)
            VALUES (?, ?, ?, ?)
        """, (
            row["medicine_name"],
            row["category"],
            row["manufacturer"],
            int(row["minimum_stock"])
        ))

    conn.commit()
    conn.close()

    print(f"{len(df)} medicines imported successfully!")


def view_medicines():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM medicines")
    medicines = cursor.fetchall()

    conn.close()
    return medicines


if __name__ == "__main__":
    import_medicines()

    medicines = view_medicines()
    print("Total medicines:", len(medicines))

