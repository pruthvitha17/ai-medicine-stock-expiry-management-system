
import sqlite3
from datetime import date


DB_NAME = "medicine_inventory.db"


def record_sale(medicine_id, quantity):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        if quantity <= 0:
            return False, "Quantity must be greater than zero."

        cursor.execute("""
            SELECT id, quantity
            FROM batches
            WHERE medicine_id = ?
            AND quantity > 0
            AND expiry_date >= ?
            ORDER BY expiry_date ASC
        """, (medicine_id, date.today().isoformat()))

        batches = cursor.fetchall()

        available_stock = sum(row[1] for row in batches)

        if available_stock < quantity:
            return False, f"Insufficient stock. Available: {available_stock}"

        remaining = quantity

        for batch_id, batch_quantity in batches:

            if remaining <= 0:
                break

            sold = min(batch_quantity, remaining)

            cursor.execute("""
                UPDATE batches
                SET quantity = quantity - ?
                WHERE id = ?
            """, (sold, batch_id))

            remaining -= sold

        cursor.execute("""
            INSERT INTO sales
            (medicine_id, quantity_sold, sale_date)
            VALUES (?, ?, ?)
        """, (medicine_id, quantity, date.today().isoformat()))

        conn.commit()

        return True, "Sale recorded and stock updated successfully!"

    except Exception as e:
        conn.rollback()
        return False, str(e)

    finally:
        conn.close()


def get_sales_history():

    conn = sqlite3.connect(DB_NAME)

    sales = conn.execute("""
        SELECT
            s.id,
            m.medicine_name,
            s.quantity_sold,
            s.sale_date
        FROM sales s
        JOIN medicines m
        ON s.medicine_id = m.id
        ORDER BY s.id DESC
    """).fetchall()

    conn.close()

    return sales
