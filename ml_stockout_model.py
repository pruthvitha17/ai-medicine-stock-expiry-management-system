
import sqlite3
import numpy as np
import pandas as pd

from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "medicine_inventory.db"

SALES_PATH = BASE_DIR / "dataset" / "medicine_sales.csv"


# --------------------------------------------------
# LOAD CURRENT MEDICINE STOCK
# --------------------------------------------------

def load_current_stock():

    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            m.id AS medicine_id,
            m.medicine_name,
            m.minimum_stock,
            COALESCE(SUM(b.quantity), 0) AS current_stock
        FROM medicines m
        LEFT JOIN batches b
            ON m.id = b.medicine_id
        GROUP BY
            m.id,
            m.medicine_name,
            m.minimum_stock
    """

    data = pd.read_sql_query(query, conn)

    conn.close()

    return data


# --------------------------------------------------
# LOAD HISTORICAL SALES
# --------------------------------------------------

def load_sales_data():

    if not SALES_PATH.exists():
        raise FileNotFoundError(
            f"Sales dataset not found: {SALES_PATH}"
        )

    sales = pd.read_csv(SALES_PATH)

    required_columns = [
        "medicine_name",
        "quantity_sold",
        "sale_date"
    ]

    for column in required_columns:
        if column not in sales.columns:
            raise ValueError(
                f"Missing column in sales dataset: {column}"
            )

    sales["sale_date"] = pd.to_datetime(
        sales["sale_date"],
        errors="coerce"
    )

    sales["quantity_sold"] = pd.to_numeric(
        sales["quantity_sold"],
        errors="coerce"
    )

    sales = sales.dropna(
        subset=[
            "medicine_name",
            "sale_date",
            "quantity_sold"
        ]
    )

    sales["month"] = (
        sales["sale_date"].dt.to_period("M")
    )

    monthly_sales = (
        sales.groupby(
            ["medicine_name", "month"]
        )["quantity_sold"]
        .sum()
        .reset_index()
    )

    return monthly_sales


# --------------------------------------------------
# CREATE SIMULATED TRAINING RECORDS
# --------------------------------------------------

def create_training_data(monthly_sales):

    records = []

    stock_scenarios = [
        0.50,
        0.75,
        1.00,
        1.25,
        1.50,
        2.00
    ]

    for medicine, group in monthly_sales.groupby(
        "medicine_name"
    ):

        group = group.sort_values("month").reset_index(
            drop=True
        )

        for i in range(2, len(group)):

            previous_demand = float(
                group.loc[i - 1, "quantity_sold"]
            )

            previous_two_average = float(
                group.loc[i - 2:i - 1, "quantity_sold"].mean()
            )

            current_demand = float(
                group.loc[i, "quantity_sold"]
            )

            demand_change = (
                previous_demand - previous_two_average
            )

            for multiplier in stock_scenarios:

                simulated_stock = (
                    previous_demand * multiplier
                )

                stockout = int(
                    current_demand > simulated_stock
                )

                records.append({

                    "medicine_name": medicine,

                    "available_stock": simulated_stock,

                    "previous_month_demand": previous_demand,

                    "previous_two_month_average":
                        previous_two_average,

                    "demand_change": demand_change,

                    "stockout": stockout,

                    "month": group.loc[i, "month"]

                })

    return pd.DataFrame(records)


# --------------------------------------------------
# TRAIN MODEL AND CALCULATE ACCURACY
# --------------------------------------------------

def train_stockout_model():

    monthly_sales = load_sales_data()

    training_data = create_training_data(
        monthly_sales
    )

    if training_data.empty:
        raise ValueError(
            "Not enough historical sales records. "
            "At least three monthly records per medicine "
            "are required."
        )

    features = [
        "available_stock",
        "previous_month_demand",
        "previous_two_month_average",
        "demand_change"
    ]

    X = training_data[features]

    y = training_data["stockout"]

    if y.nunique() < 2:
        raise ValueError(
            "Training data contains only one class. "
            "More varied sales records are required."
        )

    # Split records into training and testing sets.
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    test_model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_split=4,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42
    )

    test_model.fit(X_train, y_train)

    predictions = test_model.predict(X_test)

    accuracy = accuracy_score(
        y_test,
        predictions
    ) * 100

    print(
        f"\nDemonstration Test Accuracy: {accuracy:.2f}%"
    )

    # Train final model using all simulated records.
    final_model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_split=4,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42
    )

    final_model.fit(X, y)

    return final_model, accuracy


# --------------------------------------------------
# PREDICT CURRENT STOCKOUT RISK
# --------------------------------------------------

def predict_stockout_risk():

    monthly_sales = load_sales_data()

    current_stock_data = load_current_stock()

    if current_stock_data.empty:
        raise ValueError(
            "No medicine records found in the database."
        )

    model, accuracy = train_stockout_model()

    results = []

    for _, medicine in current_stock_data.iterrows():

        medicine_name = medicine["medicine_name"]

        medicine_history = monthly_sales[
            monthly_sales["medicine_name"] == medicine_name
        ].sort_values("month")

        if medicine_history.empty:
            previous_month_demand = 0.0
            previous_two_average = 0.0
            average_monthly_demand = 0.0
        else:

            previous_month_demand = float(
                medicine_history.iloc[-1]["quantity_sold"]
            )

            previous_two_average = float(
                medicine_history.tail(2)[
                    "quantity_sold"
                ].mean()
            )

            average_monthly_demand = float(
                medicine_history["quantity_sold"].mean()
            )

        demand_change = (
            previous_month_demand - previous_two_average
        )

        current_stock = float(
            medicine["current_stock"]
        )

        minimum_stock = float(
            medicine["minimum_stock"]
        )

        months_of_stock = (
            current_stock / average_monthly_demand
            if average_monthly_demand > 0
            else 0.0
        )

        input_data = pd.DataFrame([{

            "available_stock": current_stock,

            "previous_month_demand":
                previous_month_demand,

            "previous_two_month_average":
                previous_two_average,

            "demand_change": demand_change

        }])

        probabilities = model.predict_proba(
            input_data
        )[0]

        stockout_probability = float(
            probabilities[
                list(model.classes_).index(1)
            ] * 100
        )

        # Three risk categories.
        if stockout_probability >= 80:
            prediction = "High Stockout Risk"

        elif stockout_probability >= 60:
            prediction = "Medium Stockout Risk"

        else:
            prediction = "Low Stockout Risk"

        results.append({

            "medicine_name": medicine_name,

            "current_stock": current_stock,

            "minimum_stock": minimum_stock,

            "average_monthly_demand":
                average_monthly_demand,

            "previous_month_demand":
                previous_month_demand,

            "previous_two_month_average":
                previous_two_average,

            "demand_change": demand_change,

            "months_of_stock": months_of_stock,

            "stockout_probability":
                round(stockout_probability, 2),

            "prediction": prediction

        })

    result_data = pd.DataFrame(results)

    return result_data, accuracy


# --------------------------------------------------
# MAIN EXECUTION
# --------------------------------------------------

if __name__ == "__main__":

    try:

        data, accuracy = predict_stockout_risk()

        print("\nSTOCKOUT RISK PREDICTION")
        print("-" * 70)

        print(
            data[
                [
                    "medicine_name",
                    "current_stock",
                    "average_monthly_demand",
                    "months_of_stock",
                    "stockout_probability",
                    "prediction"
                ]
            ].to_string(index=False)
        )

        print("\nModel Accuracy: {:.2f}%".format(accuracy))

        print("\nRisk Category Summary:")

        print(
            data["prediction"].value_counts()
        )

    except Exception as error:

        print("\nError:", error)
