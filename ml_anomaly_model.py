
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "medicine_inventory.db"


def detect_ml_anomalies():

    # Read existing database without changing it
    connection = sqlite3.connect(DB_FILE)

    query = """
        SELECT
            b.id AS batch_id,
            m.medicine_name,
            b.batch_number,
            b.quantity,
            b.expiry_date,
            b.purchase_price,
            b.selling_price,
            m.minimum_stock
        FROM batches b
        JOIN medicines m ON b.medicine_id = m.id
    """

    data = pd.read_sql_query(query, connection)
    connection.close()

    if data.empty:
        raise ValueError("No batch records found in the database.")

    # Convert numeric columns
    numeric_columns = [
        "quantity",
        "purchase_price",
        "selling_price",
        "minimum_stock"
    ]

    for column in numeric_columns:
        data[column] = pd.to_numeric(
            data[column], errors="coerce"
        )

    data["expiry_date"] = pd.to_datetime(
        data["expiry_date"], errors="coerce"
    )

    # Calculate days remaining until expiry
    today = pd.Timestamp.today().normalize()

    data["days_to_expiry"] = (
        data["expiry_date"] - today
    ).dt.days

    # Prepare ML features
    features = [
        "quantity",
        "days_to_expiry",
        "purchase_price",
        "selling_price",
        "minimum_stock"
    ]

    model_data = data[features].replace(
        [np.inf, -np.inf], np.nan
    )

    model_data = model_data.fillna(
        model_data.median()
    ).fillna(0)

    if len(model_data) < 3:
        raise ValueError(
            "At least 3 batch records are required for anomaly detection."
        )

    # Train Isolation Forest
    model = IsolationForest(
        n_estimators=200,
        contamination=0.1,
        random_state=42
    )

    predictions = model.fit_predict(model_data)

    # -1 means anomaly, 1 means normal
    data["anomaly_status"] = np.where(
        predictions == -1,
        "Unusual Batch",
        "Normal Batch"
    )

    data["anomaly_score"] = model.decision_function(
        model_data
    ).round(4)

    return data.sort_values(
        "anomaly_score"
    ).reset_index(drop=True)


if __name__ == "__main__":

    results = detect_ml_anomalies()

    unusual = results[
        results["anomaly_status"] == "Unusual Batch"
    ]

    print("\n===== ML STOCK ANOMALY DETECTION =====")
    print("Algorithm: Isolation Forest")
    print("Total batches:", len(results))
    print("Unusual batches:", len(unusual))
    print("Normal batches:", len(results) - len(unusual))

    print("\nUnusual Batch Records:")

    if unusual.empty:
        print("No unusual batches detected.")
    else:
        print(
            unusual[
                [
                    "medicine_name",
                    "batch_number",
                    "quantity",
                    "days_to_expiry",
                    "anomaly_score",
                    "anomaly_status"
                ]
            ].to_string(index=False)
        )
