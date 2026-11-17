
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import date
from pathlib import Path
from qr_barcode import show_qr_barcode
from sales_management import record_sale, get_sales_history
from auth import login_screen
from database import create_tables
# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="AI-Based Medicine Stock and Expiry Management System",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent
DB_NAME = BASE_DIR / "medicine_inventory.db"
SALES_FILE = BASE_DIR / "dataset" / "medicine_sales.csv"

create_tables() 
# ---------------- LOGIN ----------------
if not st.session_state.get("logged_in", False):
    login_screen(DB_NAME)
    st.stop()

# ---------------- DATABASE ----------------
def load_data():
    conn = sqlite3.connect(DB_NAME)

    medicines = pd.read_sql_query(
        "SELECT * FROM medicines", conn
    )

    batches = pd.read_sql_query("""
        SELECT
            b.id AS batch_id,
            b.medicine_id,
            m.medicine_name,
            m.category,
            m.manufacturer,
            m.minimum_stock,
            b.batch_number,
            b.quantity,
            b.manufacturing_date,
            b.expiry_date,
            b.purchase_price,
            b.selling_price
        FROM batches b
        JOIN medicines m ON b.medicine_id = m.id
    """, conn)

    conn.close()

    if not medicines.empty:
        if not batches.empty:
            stock_qty = batches.groupby(
                "medicine_id"
            )["quantity"].sum().reset_index()
        else:
            stock_qty = pd.DataFrame(
                columns=["medicine_id", "quantity"]
            )

        stock = medicines.merge(
            stock_qty,
            left_on="id",
            right_on="medicine_id",
            how="left"
        )

        stock["quantity"] = pd.to_numeric(
            stock["quantity"], errors="coerce"
        ).fillna(0)

        stock["Stock Status"] = stock.apply(
            lambda r: "Low Stock"
            if r["quantity"] <= r["minimum_stock"]
            else "Sufficient Stock",
            axis=1
        )
    else:
        stock = pd.DataFrame()

    if not batches.empty:
        batches["quantity"] = pd.to_numeric(
            batches["quantity"], errors="coerce"
        ).fillna(0)

        batches["expiry_date"] = pd.to_datetime(
            batches["expiry_date"], errors="coerce"
        )

        batches["days_left"] = (
            batches["expiry_date"].dt.date - date.today()
        ).apply(lambda x: x.days if pd.notna(x) else None)

        def expiry_status(days):
            if pd.isna(days):
                return "Unknown"
            if days < 0:
                return "Expired"
            if days <= 30:
                return "High Risk"
            if days <= 90:
                return "Medium Risk"
            return "Safe"

        batches["Expiry Status"] = batches["days_left"].apply(
            expiry_status
        )

    return medicines, batches, stock


medicines, batches, stock = load_data()

# ---------------- SALES DATA ----------------
try:
    sales_data = pd.read_csv(SALES_FILE)

    sales_data["sale_date"] = pd.to_datetime(
        sales_data["sale_date"], errors="coerce"
    )

    sales_data["quantity_sold"] = pd.to_numeric(
        sales_data["quantity_sold"], errors="coerce"
    ).fillna(0)

    sales_data = sales_data.dropna(subset=["sale_date"])
    sales_data["Month"] = sales_data["sale_date"].dt.strftime(
        "%b %Y"
    )

except Exception:
    sales_data = pd.DataFrame()

# ---------------- DESIGN ----------------
st.markdown("""
<style>
html, body, .stApp {
    margin: 0 !important;
    padding: 0 !important;
    min-height: 100vh !important;
}

.stApp {
    background:
    linear-gradient(rgba(5,18,35,.90), rgba(5,25,40,.94)),
    url("https://images.unsplash.com/photo-1471864190281-a93a3070b6de?auto=format&fit=crop&w=2000&q=85");
    background-size: cover !important;
    background-position: center !important;
    background-attachment: fixed !important;
}

[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: transparent !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

.main .block-container {
    max-width: 100% !important;
    padding-top: .7rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}

[data-testid="stSidebar"] {
    background: #071827 !important;
    min-width: 260px !important;
}

[data-testid="stSidebar"] * {
    color: #fff !important;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2 {
    color: #5DE0D0 !important;
}

h1, h2, h3, h4, p, label, span {
    color: #F1F7FF;
}

[data-testid="stMetric"] {
    background: rgba(17,54,72,.90);
    padding: 16px;
    border-radius: 14px;
    border: 1px solid #238B91;
}

[data-testid="stMetricValue"] {
    color: #5DE0D0 !important;
}

.stButton > button {
    background: linear-gradient(90deg,#087E8B,#14A6A0);
    color: white !important;
    border: 0;
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: bold;
}

.stButton > button:hover {
    background: #15B8A6;
}

[data-testid="stDataFrame"] {
    background: rgba(12,35,52,.95);
    border-radius: 10px;
}

div[data-baseweb="select"] > div {
    background-color: #123047;
    color: white;
}

div[data-testid="stAlert"], .stAlert {
    background: rgba(8, 35, 54, 0.96) !important;
    border: 1.5px solid #36CFC5 !important;
    border-left: 5px solid #36CFC5 !important;
    border-radius: 12px !important;
    color: #FFFFFF !important;
    padding: 14px 18px !important;
}

div[data-testid="stAlert"] *, .stAlert * {
    color: #FFFFFF !important;
    opacity: 1 !important;
}

hr {
    border: none !important;
    border-top: 2px solid #39CFC5 !important;
    opacity: 0.9 !important;
    margin: 22px 0 !important;
}

div[data-testid="stDataFrame"],
div[data-testid="stTable"],
div[data-testid="stPlotlyChart"] {
    border: 1px solid rgba(75, 220, 210, 0.75) !important;
    border-radius: 12px !important;
    padding: 6px !important;
}

small, [data-testid="stCaptionContainer"] {
    color: #DCEAF5 !important;
}
</style>
""", unsafe_allow_html=True)


# ---------------- ML HELPERS ----------------
def run_all_ml_models():
    results = {}
    errors = {}

    try:
        from ml_demand_model import train_ml_demand_model
        model, future, mae, rmse = train_ml_demand_model()
        results["demand"] = {
            "future": future,
            "mae": float(mae),
            "rmse": float(rmse)
        }
    except Exception as e:
        errors["Demand forecasting"] = str(e)

    try:
        from ml_linear_model import train_linear_model
        model, mae, rmse = train_linear_model()
        results["linear"] = {
            "mae": float(mae),
            "rmse": float(rmse)
        }
    except Exception as e:
        errors["Linear Regression"] = str(e)

    try:
        from ml_anomaly_model import detect_ml_anomalies
        anomaly_df = detect_ml_anomalies()
        results["anomaly"] = anomaly_df
    except Exception as e:
        errors["Anomaly detection"] = str(e)

    try:
        from ml_stockout_model import predict_stockout
        stockout_df, accuracy = predict_stockout()
        results["stockout"] = {
            "data": stockout_df,
            "accuracy": accuracy
        }
    except Exception as e:
        errors["Stockout prediction"] = str(e)

    st.session_state["ml_results"] = results
    st.session_state["ml_errors"] = errors


def show_ml_dashboard():
    st.subheader("🤖 ML Intelligence Dashboard")

    st.write(
        "Machine learning analyses medicine demand, estimates stockout risk, "
        "and identifies unusual inventory batches."
    )

    st.info(
        "Demo limitation: the sales dataset contains synthetic sample records. "
        "Stockout labels are generated from stock and demand rules. Treat all "
        "outputs as project demonstrations, not dependable pharmacy forecasts."
    )

    if st.button("🚀 Run / Refresh All ML Models", type="primary"):
        with st.spinner("Training and running the four ML models..."):
            run_all_ml_models()

    results = st.session_state.get("ml_results")
    errors = st.session_state.get("ml_errors", {})

    if not results:
        st.warning(
            "Click 'Run / Refresh All ML Models' to generate the ML dashboard."
        )
        st.markdown("#### Models included")

        model_cols = st.columns(4)
        model_cols[0].metric("Demand Forecast", "Random Forest")
        model_cols[1].metric("Model Comparison", "Linear Regression")
        model_cols[2].metric("Anomaly Detection", "Isolation Forest")
        model_cols[3].metric("Stockout Risk", "Random Forest")
        return

    demand_result = results.get("demand")
    linear_result = results.get("linear")
    anomaly_df = results.get("anomaly")
    stockout_result = results.get("stockout")

    high_risk_count = 0

    if stockout_result and isinstance(
        stockout_result.get("data"), pd.DataFrame
    ):
        s_df = stockout_result["data"]

        if "prediction" in s_df.columns:
            high_risk_count = int(
                (s_df["prediction"] == "High Stockout Risk").sum()
            )

    unusual_count = 0

    if isinstance(anomaly_df, pd.DataFrame) and not anomaly_df.empty:
        status_col = next(
            (c for c in anomaly_df.columns if c.lower() in
             ["anomaly_status", "anomaly", "status", "prediction"]),
            None
        )

        if status_col:
            unusual_count = int(
                anomaly_df[status_col].astype(str).str.lower()
                .str.contains("unusual|anomaly|outlier").sum()
            )

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Medicines in Inventory", len(medicines))
    k2.metric("High Stockout Risk", high_risk_count)
    k3.metric("Unusual Batches", unusual_count)
    k4.metric("ML Models Executed", f"{len(results)}/4")

    st.markdown("---")

    left, right = st.columns(2)

    with left:
        st.markdown("### 📈 Random Forest Demand Forecast")

        if demand_result:
            future = demand_result["future"]

            st.metric(
                "Demand Model MAE",
                f'{demand_result["mae"]:.2f}'
            )

            st.metric(
                "Demand Model RMSE",
                f'{demand_result["rmse"]:.2f}'
            )

            if isinstance(future, pd.DataFrame) and not future.empty:
                st.dataframe(
                    future,
                    use_container_width=True,
                    hide_index=True
                )

                if {
                    "medicine_name", "predicted_demand"
                }.issubset(future.columns):
                    chart = future.nlargest(
                        15, "predicted_demand"
                    )

                    fig = px.bar(
                        chart,
                        x="medicine_name",
                        y="predicted_demand",
                        title="Top 15 Predicted Medicine Demand"
                    )

                    fig.update_layout(template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Demand model did not run successfully.")

    with right:
        st.markdown("### ⚠️ Random Forest Stockout Risk")

        if stockout_result:
            stockout_df = stockout_result["data"]
            accuracy = stockout_result["accuracy"]

            if accuracy is None:
                st.metric("Demo Test Accuracy", "Not available")
            else:
                st.metric(
                    "Demo Test Accuracy",
                    f"{float(accuracy):.2f}%"
                )

            if isinstance(stockout_df, pd.DataFrame) and not stockout_df.empty:
                show_cols = [
                    c for c in [
                        "medicine_name",
                        "current_stock",
                        "minimum_stock",
                        "average_monthly_demand",
                        "months_of_stock",
                        "stockout_probability",
                        "prediction"
                    ] if c in stockout_df.columns
                ]

                st.dataframe(
                    stockout_df[show_cols],
                    use_container_width=True,
                    hide_index=True
                )

                if {
                    "medicine_name", "stockout_probability"
                }.issubset(stockout_df.columns):
                    fig = px.bar(
                        stockout_df.head(15),
                        x="medicine_name",
                        y="stockout_probability",
                        title="Estimated Stockout Risk Score (%)"
                    )

                    fig.update_layout(
                        template="plotly_dark",
                        yaxis_range=[0, 100]
                    )

                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Stockout model did not run successfully.")

    st.markdown("---")
    st.markdown("### 📊 Demand Model Performance Comparison")

    if demand_result and linear_result:
        comparison = pd.DataFrame({
            "Algorithm": [
                "Random Forest Regressor",
                "Linear Regression"
            ],
            "MAE": [
                demand_result["mae"],
                linear_result["mae"]
            ],
            "RMSE": [
                demand_result["rmse"],
                linear_result["rmse"]
            ]
        })

        st.dataframe(
            comparison.round(2),
            use_container_width=True,
            hide_index=True
        )

        fig = px.bar(
            comparison,
            x="Algorithm",
            y=["MAE", "RMSE"],
            barmode="group",
            title="Regression Model Error Comparison"
        )

        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(
            "Both regression models must run to show the comparison."
        )

    st.markdown("---")
    st.markdown("### 🔍 Isolation Forest Batch Anomaly Detection")

    if isinstance(anomaly_df, pd.DataFrame):
        st.metric("Batch Records Analysed", len(anomaly_df))

        if not anomaly_df.empty:
            status_col = next(
                (c for c in anomaly_df.columns if c.lower() in
                 ["anomaly_status", "anomaly", "status", "prediction"]),
                None
            )

            if status_col:
                unusual = anomaly_df[
                    anomaly_df[status_col].astype(str).str.lower()
                    .str.contains("unusual|anomaly|outlier")
                ]

                st.metric("Records Flagged as Unusual", len(unusual))

                st.dataframe(
                    unusual if not unusual.empty else anomaly_df,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.dataframe(
                    anomaly_df,
                    use_container_width=True,
                    hide_index=True
                )

    elif "anomaly" not in results:
        st.warning("Anomaly model did not run successfully.")

    if errors:
        st.markdown("---")
        st.markdown("### Model execution messages")

        for model_name, message in errors.items():
            st.error(f"{model_name}: {message}")

    st.caption(
        "MAE and RMSE are error measures (lower is better). Stockout score is "
        "a model estimate based on demonstration labels, not a calibrated probability."
    )


# ---------------- SIDEBAR ----------------
st.sidebar.title("💊 Medicine AI System")

role = st.session_state.get("role", "user")

if role == "admin":
    st.sidebar.success("👨‍💼 Admin Account")
    page = st.sidebar.selectbox(
        "Select Module",
        [
            "🤖 ML Intelligence Dashboard",
            "💊 Medicine Inventory",
            "💰 Sales Management",
            "⏰ Expiry Management",
            "📈 Demand Overview",
            "⚠️ Wastage Management",
            "🔍 Anomaly Detection",
            "📦 FEFO Management",
            "QR & Barcode"
        ]
    )
else:
    st.sidebar.success(
        "👤 User Account: " +
        st.session_state.get("full_name", "")
    )
    page = "Medicine Information"

if st.sidebar.button("🚪 Logout"):
    for key in [
        "logged_in", "role", "username", "full_name",
        "ml_results", "ml_errors", "anomaly_page_results"
    ]:
        st.session_state.pop(key, None)

    st.rerun()


# ---------------- HEADER ----------------
st.title("💊 AI-Based Medicine Stock and Expiry Management System")
st.caption(
    "Machine Learning-Based Medicine Demand, Stockout and Inventory Analysis"
)


# =====================================================
# USER DASHBOARD - READ ONLY
# =====================================================
if page == "Medicine Information":

    st.subheader("💊 Medicine Information")

    st.write(
        "Welcome! You can view medicine details, available stock "
        "and expiry information."
    )

    if not stock.empty:
        search = st.text_input("🔎 Search Medicine")

        user_stock = stock.copy()

        if search:
            user_stock = user_stock[
                user_stock["medicine_name"].astype(str).str.contains(
                    search, case=False, na=False
                )
            ]

        user_cols = [
            c for c in [
                "medicine_name",
                "category",
                "manufacturer",
                "quantity",
                "Stock Status"
            ] if c in user_stock.columns
        ]

        st.markdown("### 💊 Available Medicines")

        st.dataframe(
            user_stock[user_cols],
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No medicine records available.")

    st.markdown("---")
    st.subheader("⏰ Medicine Expiry Information")

    if not batches.empty:
        user_batch_cols = [
            "medicine_name",
            "batch_number",
            "quantity",
            "expiry_date",
            "Expiry Status"
        ]

        st.dataframe(
            batches[user_batch_cols],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No batch information available.")


# =====================================================
# MAIN ML DASHBOARD - ADMIN
# =====================================================
elif page == "🤖 ML Intelligence Dashboard":
    show_ml_dashboard()


# =====================================================
# MEDICINE INVENTORY
# =====================================================
elif page == "💊 Medicine Inventory":

    st.subheader("💊 Complete Medicine Inventory")

    if not stock.empty:
        search = st.text_input("🔎 Search Medicine")
        filtered = stock.copy()

        if search:
            filtered = filtered[
                filtered["medicine_name"].astype(str).str.contains(
                    search, case=False, na=False
                )
            ]

        show_cols = [
            c for c in [
                "id", "medicine_name", "category", "manufacturer",
                "quantity", "minimum_stock", "Stock Status"
            ] if c in filtered.columns
        ]

        st.dataframe(
            filtered[show_cols],
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇ Download Inventory CSV",
            filtered.to_csv(index=False),
            "medicine_inventory.csv",
            "text/csv"
        )

        st.subheader("📦 Batch Details")

        if not batches.empty:
            st.dataframe(
                batches,
                use_container_width=True,
                hide_index=True
            )
    else:
        st.warning("No medicine records found.")


# =====================================================
# SALES MANAGEMENT
# =====================================================
elif page == "💰 Sales Management":

    st.subheader("💰 Medicine Sales Management")

    st.write(
        "Record medicine sales and automatically update available batch stock."
    )

    if medicines.empty:
        st.warning("No medicines available.")
    else:
        with st.form("sales_form"):
            medicine_options = dict(
                zip(medicines["medicine_name"], medicines["id"])
            )

            selected_medicine = st.selectbox(
                "Select Medicine",
                list(medicine_options.keys())
            )

            quantity = st.number_input(
                "Quantity Sold",
                min_value=1,
                step=1
            )

            submitted = st.form_submit_button("Record Sale")

            if submitted:
                success, message = record_sale(
                    int(medicine_options[selected_medicine]),
                    int(quantity)
                )

                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    st.markdown("---")
    st.subheader("📋 Sales History")

    history = get_sales_history()

    history_df = pd.DataFrame(
        history,
        columns=[
            "Sale ID",
            "Medicine Name",
            "Quantity Sold",
            "Sale Date"
        ]
    )

    if not history_df.empty:
        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Units Sold",
            int(history_df["Quantity Sold"].sum())
        )

        st.download_button(
            "⬇ Download Sales History",
            history_df.to_csv(index=False),
            "sales_history.csv",
            "text/csv"
        )
    else:
        st.info("No sales have been recorded yet.")


# =====================================================
# EXPIRY MANAGEMENT
# =====================================================
elif page == "⏰ Expiry Management":

    st.subheader("⏰ Medicine Expiry Management")

    st.caption(
        "Expiry categories are calculated from expiry dates using rules; "
        "this page is not an ML prediction."
    )

    if not batches.empty:
        status_filter = st.selectbox(
            "Filter Expiry Status",
            [
                "All", "Expired", "High Risk",
                "Medium Risk", "Safe", "Unknown"
            ]
        )

        expiry_view = batches.copy()

        if status_filter != "All":
            expiry_view = expiry_view[
                expiry_view["Expiry Status"] == status_filter
            ]

        cols = [
            c for c in [
                "medicine_name", "batch_number", "quantity",
                "expiry_date", "days_left", "Expiry Status"
            ] if c in expiry_view.columns
        ]

        st.dataframe(
            expiry_view[cols],
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇ Download Expiry Report",
            expiry_view.to_csv(index=False),
            "expiry_report.csv",
            "text/csv"
        )
    else:
        st.info("No batch records found.")


# =====================================================
# DEMAND OVERVIEW
# =====================================================
elif page == "📈 Demand Overview":

    st.subheader("📈 Historical Medicine Demand")

    if not sales_data.empty:
        demand = sales_data.groupby(
            "medicine_name"
        )["quantity_sold"].sum().reset_index()

        demand = demand.sort_values(
            "quantity_sold", ascending=False
        )

        fig = px.bar(
            demand.head(15),
            x="medicine_name",
            y="quantity_sold",
            title="Top 15 Medicines by Historical Sales"
        )

        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            demand,
            use_container_width=True,
            hide_index=True
        )

        monthly = sales_data.groupby(
            "Month"
        )["quantity_sold"].sum().reset_index()

        fig2 = px.line(
            monthly,
            x="Month",
            y="quantity_sold",
            markers=True,
            title="Historical Monthly Sales"
        )

        fig2.update_layout(template="plotly_dark")
        st.plotly_chart(fig2, use_container_width=True)

        st.download_button(
            "⬇ Download Demand Data",
            sales_data.to_csv(index=False),
            "demand_data.csv",
            "text/csv"
        )
    else:
        st.info("No demand data available.")


# =====================================================
# WASTAGE MANAGEMENT
# =====================================================
elif page == "⚠️ Wastage Management":

    st.subheader("⚠️ Medicine Wastage Management")

    if not batches.empty:
        wastage = batches[
            batches["Expiry Status"].isin(
                ["Expired", "High Risk", "Medium Risk"]
            )
        ].copy()

        st.metric(
            "Total At-Risk Stock",
            int(wastage["quantity"].sum())
        )

        st.dataframe(
            wastage[
                [
                    "medicine_name",
                    "batch_number",
                    "quantity",
                    "expiry_date",
                    "Expiry Status"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇ Download Wastage Report",
            wastage.to_csv(index=False),
            "wastage_report.csv",
            "text/csv"
        )
    else:
        st.info("No batch records found.")


# =====================================================
# ANOMALY DETECTION
# =====================================================
elif page == "🔍 Anomaly Detection":

    st.subheader("🔍 ML-Based Unusual Batch Detection")

    st.write(
        "This module uses the Isolation Forest model to flag unusual batch records."
    )

    if st.button("Run Isolation Forest"):
        try:
            from ml_anomaly_model import detect_ml_anomalies

            anomaly_df = detect_ml_anomalies()

            st.session_state["anomaly_page_results"] = anomaly_df

        except Exception as e:
            st.error(f"Anomaly detection error: {e}")

    anomaly_df = st.session_state.get("anomaly_page_results")

    if isinstance(anomaly_df, pd.DataFrame):
        st.metric("Records Analysed", len(anomaly_df))

        if not anomaly_df.empty:
            status_col = next(
                (c for c in anomaly_df.columns if c.lower() in
                 ["anomaly_status", "anomaly", "status", "prediction"]),
                None
            )

            if status_col:
                flagged = anomaly_df[
                    anomaly_df[status_col].astype(str).str.lower()
                    .str.contains("unusual|anomaly|outlier")
                ]

                st.metric("Unusual Records", len(flagged))

                st.dataframe(
                    flagged if not flagged.empty else anomaly_df,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.dataframe(
                    anomaly_df,
                    use_container_width=True,
                    hide_index=True
                )
    else:
        st.info("Click the button to run the ML anomaly model.")


# =====================================================
# FEFO MANAGEMENT
# =====================================================
elif page == "📦 FEFO Management":

    st.subheader("📦 FEFO - First Expiry, First Out")

    if not batches.empty:
        fefo = batches[
            (batches["quantity"] > 0) &
            (batches["expiry_date"].notna()) &
            (batches["expiry_date"].dt.date >= date.today())
        ].sort_values(
            "expiry_date",
            ascending=True
        )

        st.info(
            "Use the batch with the earliest eligible expiry date first."
        )

        st.dataframe(
            fefo[
                [
                    "medicine_name",
                    "batch_number",
                    "quantity",
                    "expiry_date",
                    "Expiry Status"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No batch records available.")


# =====================================================
# QR & BARCODE
# =====================================================
elif page == "QR & Barcode":
    show_qr_barcode()
