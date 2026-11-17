
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "dataset" / "medicine_sales.csv"


def train_ml_demand_model():

    # Read existing sales data without changing the CSV
    data = pd.read_csv(DATA_FILE)

    required = {"medicine_name", "quantity_sold", "sale_date"}
    if not required.issubset(data.columns):
        raise ValueError("Required columns are missing from sales CSV.")

    data["sale_date"] = pd.to_datetime(data["sale_date"], errors="coerce")
    data["quantity_sold"] = pd.to_numeric(
        data["quantity_sold"], errors="coerce"
    )

    data = data.dropna(
        subset=["medicine_name", "sale_date", "quantity_sold"]
    ).copy()

    # Create time-based features
    data["year"] = data["sale_date"].dt.year
    data["month"] = data["sale_date"].dt.month

    # Group monthly sales for each medicine
    monthly = (
        data.groupby(
            ["medicine_name", "year", "month"],
            as_index=False
        )["quantity_sold"].sum()
    )

    monthly["month_date"] = pd.to_datetime(
        monthly["year"].astype(str)
        + "-"
        + monthly["month"].astype(str)
        + "-01"
    )

    monthly = monthly.sort_values("month_date")

    # Previous month's demand for each medicine
    monthly["previous_month_sales"] = (
        monthly.groupby("medicine_name")["quantity_sold"].shift(1)
    )

    monthly["month_number"] = monthly["month_date"].dt.month

    monthly = monthly.dropna().copy()

    if len(monthly) < 10:
        raise ValueError(
            "Not enough historical monthly records for ML training."
        )

    features = [
        "previous_month_sales",
        "month_number"
    ]

    # Chronological train/test split
    monthly = monthly.sort_values("month_date")
    split = int(len(monthly) * 0.8)

    train = monthly.iloc[:split]
    test = monthly.iloc[split:]

    if train.empty or test.empty:
        raise ValueError("Not enough data for training and testing.")

    # Encode medicine names
    X_train = pd.get_dummies(
        train[features + ["medicine_name"]],
        columns=["medicine_name"]
    )

    X_test = pd.get_dummies(
        test[features + ["medicine_name"]],
        columns=["medicine_name"]
    )

    X_test = X_test.reindex(
        columns=X_train.columns,
        fill_value=0
    )

    y_train = train["quantity_sold"]
    y_test = test["quantity_sold"]

    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42,
        min_samples_leaf=1
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))

    # Estimate next month using each medicine's latest sales
    latest = monthly.sort_values("month_date").groupby(
        "medicine_name"
    ).tail(1).copy()

    next_dates = latest["month_date"] + pd.offsets.MonthBegin(1)

    future = pd.DataFrame({
        "medicine_name": latest["medicine_name"].values,
        "previous_month_sales": latest["quantity_sold"].values,
        "month_number": next_dates.dt.month.values
    })

    X_future = pd.get_dummies(
        future[features + ["medicine_name"]],
        columns=["medicine_name"]
    )

    X_future = X_future.reindex(
        columns=X_train.columns,
        fill_value=0
    )

    future["predicted_demand"] = np.maximum(
        0, np.round(model.predict(X_future))
    ).astype(int)

    return model, future, mae, rmse


if __name__ == "__main__":

    model, predictions, mae, rmse = train_ml_demand_model()

    print("\n===== MEDICINE DEMAND ML MODEL =====")
    print("Algorithm: Random Forest Regressor")
    print("MAE:", round(mae, 2))
    print("RMSE:", round(rmse, 2))

    print("\nNext Month Demand Predictions:")
    print(predictions[
        ["medicine_name", "predicted_demand"]
    ].to_string(index=False))
