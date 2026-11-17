
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "dataset" / "medicine_sales.csv"


def train_linear_model():

    data = pd.read_csv(DATA_FILE)

    data["sale_date"] = pd.to_datetime(
        data["sale_date"], errors="coerce"
    )
    data["quantity_sold"] = pd.to_numeric(
        data["quantity_sold"], errors="coerce"
    )

    data = data.dropna(
        subset=["medicine_name", "sale_date", "quantity_sold"]
    )

    data["year"] = data["sale_date"].dt.year
    data["month"] = data["sale_date"].dt.month

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

    monthly["previous_month_sales"] = (
        monthly.groupby("medicine_name")["quantity_sold"].shift(1)
    )

    monthly["month_number"] = monthly["month_date"].dt.month
    monthly = monthly.dropna().copy()

    if len(monthly) < 10:
        raise ValueError("Not enough historical data for training.")

    features = [
        "previous_month_sales",
        "month_number"
    ]

    split = int(len(monthly) * 0.8)

    train = monthly.iloc[:split]
    test = monthly.iloc[split:]

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

    model = LinearRegression()
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))

    return model, mae, rmse


if __name__ == "__main__":

    model, mae, rmse = train_linear_model()

    print("\n===== LINEAR REGRESSION MODEL =====")
    print("Algorithm: Linear Regression")
    print("MAE:", round(mae, 2))
    print("RMSE:", round(rmse, 2))

    print("\nModel training and evaluation completed!")
