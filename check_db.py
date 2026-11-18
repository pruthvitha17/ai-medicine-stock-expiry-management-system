import sqlite3

conn = sqlite3.connect("medicine_inventory.db")
cursor = conn.cursor()

tables = cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

print("Tables:", tables)

for table in ["medicines", "batches", "sales"]:
    count = cursor.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]
    print(table, ":", count)

conn.close()