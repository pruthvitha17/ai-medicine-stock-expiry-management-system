
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor

DATA_PATH = "dataset/medicine_sales.csv"
MODEL_PATH = "models/demand_model.pkl"


def train_demand_model():

    df = pd.read_csv(DATA_PATH)

    df["sale_date"] = pd.to_datetime(df["sale_date"])

    df["month"] = df["sale_date"].dt.month
    df["year"] = df["sale_date"].dt.year

    predictions = []

    for medicine in df["medicine_name"].unique():

        medicine_data = df[
            df["medicine_name"] == medicine
        ].copy()

        X = medicine_data[["month", "year"]]
        y = medicine_data["quantity_sold"]

        model = RandomForestRegressor(
            n_estimators=100,
            random_state=42
        )

        model.fit(X, y)

        next_month = medicine_data["month"].max() + 1
        next_year = medicine_data["year"].max()

        if next_month > 12:
            next_month = 1
            next_year += 1

        future_data = pd.DataFrame({
            "month": [next_month],
            "year": [next_year]
        })

        predicted_demand = model.predict(future_data)[0]

        predictions.append({
            "medicine_name": medicine,
            "predicted_demand": round(
                max(0, predicted_demand), 2
            )
        })

    return pd.DataFrame(predictions)


if __name__ == "__main__":

    results = train_demand_model()

    print("\nMEDICINE DEMAND PREDICTION")
    print("-" * 45)

    print(results.to_string(index=False))

    print("-" * 45)
    print("Total medicines predicted:", len(results))
