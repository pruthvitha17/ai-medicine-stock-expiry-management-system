
import sqlite3
conn = sqlite3.connect("medicine_inventory.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT id, medicine_id
    FROM batches
    WHERE purchase_price = 0 OR selling_price = 0
""")

batches = cursor.fetchall()

for batch_id, medicine_id in batches:

    # Demonstration prices only
    purchase_price = round(5 + (medicine_id % 20), 2)
    selling_price = round(purchase_price * 1.5, 2)

    cursor.execute("""
        UPDATE batches
        SET purchase_price = ?,
            selling_price = ?
        WHERE id = ?
    """, (purchase_price, selling_price, batch_id))

conn.commit()

print(len(batches), "batch prices updated successfully!")

cursor.execute("""
    SELECT m.medicine_name, b.batch_number,
           b.purchase_price, b.selling_price
    FROM batches b
    JOIN medicines m ON b.medicine_id = m.id
    ORDER BY m.medicine_name
""")

for row in cursor.fetchall():
    print(row)

conn.close()
