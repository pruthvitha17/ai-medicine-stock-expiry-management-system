
import sqlite3

conn = sqlite3.connect("medicine_inventory.db")
cursor = conn.cursor()

# Select 5 medicines that have batches
cursor.execute("""
    SELECT m.id, m.medicine_name, m.minimum_stock
    FROM medicines m
    WHERE EXISTS (
        SELECT 1 FROM batches b
        WHERE b.medicine_id = m.id
    )
    ORDER BY m.id
    LIMIT 5
""")

medicines = cursor.fetchall()

for medicine_id, name, minimum_stock in medicines:

    # Set total stock below minimum stock
    new_quantity = max(0, minimum_stock - 5)

    cursor.execute("""
        SELECT id FROM batches
        WHERE medicine_id = ?
        ORDER BY id
    """, (medicine_id,))

    batch_ids = cursor.fetchall()

    for index, (batch_id,) in enumerate(batch_ids):
        quantity = new_quantity if index == 0 else 0

        cursor.execute("""
            UPDATE batches
            SET quantity = ?
            WHERE id = ?
        """, (quantity, batch_id))

    print(
        name,
        "- Minimum Stock:", minimum_stock,
        "- Available Stock:", new_quantity,
        "- LOW STOCK"
    )

conn.commit()
conn.close()

print("\n5 medicines updated with low stock!")
