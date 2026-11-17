
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "medicine_inventory.db"
SALES_FILE = BASE_DIR / "dataset" / "medicine_sales.csv"


def predict_stockout():

    # 1. Get medicine stock from database
    conn = sqlite3.connect(DB_FILE)

    query = """
    SELECT
        m.medicine_name,
        COALESCE(SUM(b.quantity), 0) AS current_stock,
        m.minimum_stock
    FROM medicines m
    LEFT JOIN batches b
        ON m.id = b.medicine_id
        AND date(b.expiry_date) >= date('now')
    GROUP BY m.id, m.medicine_name, m.minimum_stock
    """

    stock = pd.read_sql_query(query, conn)
    conn.close()

    if stock.empty:
        return pd.DataFrame(), None

    # 2. Read existing sales dataset
    sales = pd.read_csv(SALES_FILE)

    sales["quantity_sold"] = pd.to_numeric(
        sales["quantity_sold"], errors="coerce"
    ).fillna(0)

    # 3. Calculate average monthly demand
    demand = (
        sales.groupby("medicine_name")["quantity_sold"]
        .mean()
        .reset_index()
        .rename(columns={
            "quantity_sold": "average_monthly_demand"
        })
    )

    # 4. Combine stock and demand
    data = stock.merge(
        demand,
        on="medicine_name",
        how="left"
    )

    numeric_columns = [
        "current_stock",
        "minimum_stock",
        "average_monthly_demand"
    ]

    for col in numeric_columns:
        data[col] = pd.to_numeric(
            data[col], errors="coerce"
        ).fillna(0)

    # 5. Calculate months of available stock
    data["months_of_stock"] = np.where(
        data["average_monthly_demand"] > 0,
        data["current_stock"] /
        data["average_monthly_demand"],
        999
    )

    # 6. Create balanced demonstration risk labels
    # Medicines with the lowest stock coverage are high risk.
    # This is a relative demonstration label, not a real outcome.
    data["risk_rank"] = data["months_of_stock"].rank(
        method="first",
        ascending=True
    )

    total = len(data)

    if total >= 2:
        high_risk_count = max(1, int(np.ceil(total * 0.40)))
        data["risk_label"] = (
            data["risk_rank"] <= high_risk_count
        ).astype(int)
    else:
        data["risk_label"] = 1

    # 7. Prepare model features
    features = [
        "current_stock",
        "minimum_stock",
        "average_monthly_demand",
        "months_of_stock"
    ]

    X = data[features].replace(
        [np.inf, -np.inf], np.nan
    ).fillna(0)

    y = data["risk_label"]

    accuracy = None

    # 8. Train Random Forest when enough examples exist
    if len(data) >= 8 and y.nunique() == 2:

        model = RandomForestClassifier(
            n_estimators=150,
            max_depth=4,
            min_samples_leaf=3,
            class_weight="balanced",
            random_state=42
        )

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.25,
            random_state=42,
            stratify=y
        )

        # Evaluate model on unseen test records
        test_model = RandomForestClassifier(
            n_estimators=150,
            max_depth=4,
            min_samples_leaf=3,
            class_weight="balanced",
            random_state=42
        )

        test_model.fit(X_train, y_train)

        test_predictions = test_model.predict(X_test)

        accuracy = accuracy_score(
            y_test, test_predictions
        ) * 100

        # Train final model on all available records
        model.fit(X, y)

        risk_index = list(model.classes_).index(1)

        data["stockout_probability"] = (
            model.predict_proba(X)[:, risk_index] * 100
        )

    else:
        # Fallback for very small datasets
        data["stockout_probability"] = (
            data["risk_rank"] / max(total, 1) * 100
        )

    # 9. Assign risk category
    data["prediction"] = np.where(
        data["stockout_probability"] >= 50,
        "High Stockout Risk",
        "Low Stockout Risk"
    )

    # 10. Sort high-risk medicines first
    data = data.sort_values(
        "stockout_probability",
        ascending=False
    ).reset_index(drop=True)

    data = data.drop(
        columns=["risk_rank", "risk_label"],
        errors="ignore"
    )

    return data, accuracy


if __name__ == "__main__":

    print("\n===== STOCKOUT PREDICTION MODEL =====")

    result, accuracy = predict_stockout()

    if not result.empty:

        print("\nStockout Prediction Results:\n")
        print(result.to_string(index=False))

        if accuracy is not None:
            print(f"\nDemo Test Accuracy: {accuracy:.2f}%")
        else:
            print("\nAccuracy: Not available")

    else:
        print("No medicine records found.")
