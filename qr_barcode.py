
import streamlit as st
import sqlite3
import pandas as pd
import qrcode
import barcode
from barcode.writer import ImageWriter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_NAME = BASE_DIR / "medicine_inventory.db"


def show_qr_barcode():

    st.header("QR Code & Barcode Management")

    conn = sqlite3.connect(DB_NAME)

    medicines = pd.read_sql_query("""
        SELECT DISTINCT m.medicine_name
        FROM medicines m
        JOIN batches b ON m.id = b.medicine_id
        ORDER BY m.medicine_name
    """, conn)

    conn.close()

    if medicines.empty:
        st.warning("No medicines found.")
        return

    selected_medicine = st.selectbox(
        "Search Medicine",
        medicines["medicine_name"].tolist()
    )

    conn = sqlite3.connect(DB_NAME)

    batches = conn.execute("""
        SELECT b.batch_number, b.quantity, b.expiry_date
        FROM medicines m
        JOIN batches b ON m.id = b.medicine_id
        WHERE m.medicine_name = ?
    """, (selected_medicine,)).fetchall()

    conn.close()

    for batch_number, quantity, expiry_date in batches:

        st.subheader(f"Batch: {batch_number}")

        st.write("Medicine:", selected_medicine)
        st.write("Stock:", quantity)
        st.write("Expiry Date:", expiry_date)

        # Generate QR Code
        data = (
            f"Medicine: {selected_medicine}\n"
            f"Batch: {batch_number}\n"
            f"Stock: {quantity}\n"
            f"Expiry Date: {expiry_date}"
        )

        qr = qrcode.make(data)

        st.image(
            qr.convert("RGB"),
            caption="Medicine QR Code",
            width=200
        )

        # Generate Barcode
        code = barcode.get(
            "code128",
            str(batch_number),
            writer=ImageWriter()
        )

        barcode_image = code.render()

        st.image(
            barcode_image.convert("RGB"),
            caption="Medicine Barcode",
            width=300
        )

        st.divider()
