
import sqlite3
import pandas as pd
from sklearn.ensemble import IsolationForest

DB_NAME = "medicine_inventory.db"


def detect_anomalies():

    conn = sqlite3.connect(DB_NAME)

    df = pd.read_sql_query("""
        SELECT m.medicine_name,
               b.batch_number,
               b.quantity
        FROM batches b
        JOIN medicines m ON b.medicine_id = m.id
    """, conn)

    conn.close()

    if len(df) < 2:
        return df

    model = IsolationForest(
        contamination=0.1,
        random_state=42
    )

    df["prediction"] = model.fit_predict(
        df[["quantity"]]
    )

    df["status"] = df["prediction"].apply(
        lambda x: "Unusual Stock" if x == -1
        else "Normal Stock"
    )

    return df[[
        "medicine_name",
        "batch_number",
        "quantity",
        "status"
    ]]


if __name__ == "__main__":

    print("STOCK ANOMALY DETECTION")
    print("-" * 50)

    results = detect_anomalies()

    print(results.to_string(index=False))

    print("-" * 50)
    print("Total batches checked:", len(results))
    print(
        "Unusual stock records:",
        (results["status"] == "Unusual Stock").sum()
    )
