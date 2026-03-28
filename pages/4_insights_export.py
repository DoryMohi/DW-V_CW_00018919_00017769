import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import json
from datetime import datetime
from utils import detect_id_columns



st.set_page_config(page_title="Insights & Export", layout="wide")

st.title("📊 Page D — Insights & Export Dashboard")

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data(data):
    return data.copy()

df = st.session_state.get("df", None)

if df is None or df.empty:
    st.error("No dataset found. Please upload and process data first.")
    st.stop()

df = load_data(df)

st.caption("Dataset loaded successfully")

# =========================
# DATASET OVERVIEW
# =========================
st.subheader("📌 Dataset Overview")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Rows", df.shape[0])
col2.metric("Columns", df.shape[1])
col3.metric("Missing Values", int(df.isnull().sum().sum()))
col4.metric("Duplicate Rows", int(df.duplicated().sum()))



missing = df.isnull().sum().sum()
duplicates = df.duplicated().sum()
ignore_cols = detect_id_columns(df)
st.divider()
# =========================
# COLUMN TYPES
# =========================
st.subheader("📂 Column Analysis")

st.markdown("""
<style>
.card {
    padding: 20px;
    border-radius: 14px;
    background-color: #f8f9fb;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
categorical_cols = df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()

col1, col2 = st.columns(2)

def show_tags(cols):
    tags = " ".join([
        f"<span style='padding:4px 10px; margin:4px; background:#eef; border-radius:10px; display:inline-block; font-size:13px'>{col}</span>"
        for col in cols
    ])
    st.markdown(tags, unsafe_allow_html=True)

with col1:
    st.markdown(f"**🔢 Numeric ({len(numeric_cols)})**")
    show_tags(numeric_cols)

with col2:
    st.markdown(f"**🏷 Categorical ({len(categorical_cols)})**")
    show_tags(categorical_cols)

st.divider()
# =========================
# SMART INSIGHTS
# =========================
st.subheader("🧠 Smart Insights")

if numeric_cols:
    selected_num = st.selectbox("Select numeric column", numeric_cols)

    data = df[selected_num].dropna()

    if not data.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Mean", round(data.mean(), 2))
        c2.metric("Median", round(data.median(), 2))
        c3.metric("Std Dev", round(data.std(), 2))

        st.write(f"Min: {data.min()} | Max: {data.max()}")

        cv = data.std() / (data.mean() + 1e-9)

        if cv > 0.5:
            variability = "high variability"
        elif cv > 0.2:
            variability = "moderate variability"
        else:
            variability = "low variability"

        st.info(
            f"The average **{selected_num}** is **{round(data.mean(),2)}**. "
            f"Values range from {data.min()} to {data.max()}, indicating {variability}."
        )
st.divider()
# =========================
# CATEGORICAL INSIGHTS
# =========================
if categorical_cols:
    st.subheader("🏷 Categorical Insights")

    selected_cat = st.selectbox("Select categorical column", categorical_cols)

    value_counts = df[selected_cat].value_counts()

    if value_counts.empty:
        st.warning("No data available")
    else:
        top = value_counts.head(10)

        total = value_counts.sum()
        top_pct = (top.iloc[0] / total) * 100       

        st.dataframe(top)

        st.info(
            f"'{top.index[0]}' dominates with {top.iloc[0]} occurrences "
            f"({top_pct:.1f}% of data), indicating "
            f"{'imbalance' if top_pct > 60 else 'fair distribution'}."
        )
st.divider()
# =========================
# ADVANCED ANALYSIS
# =========================
st.subheader("📊 Advanced Analysis")

if numeric_cols and categorical_cols:

    cat_col = st.selectbox("Group by", categorical_cols, key="group_cat")
    num_col = st.selectbox("Measure", numeric_cols, key="group_num")

    grouped = df.groupby(cat_col)[num_col].mean().sort_values(ascending=False).head(10)

    st.dataframe(grouped)

    overall_mean = df[num_col].mean()
    top_category = grouped.index[0]
    top_value = grouped.iloc[0]

    std = df[num_col].std()

    st.caption(
        f"Overall variability (std) is {round(std,2)}, indicating "
        f"{'high dispersion' if std > overall_mean * 0.5 else 'stable values'}."
    )

    st.success(
        f"'{top_category}' has the highest average {num_col} ({round(top_value,2)}), "
        f"which is {'above' if top_value > overall_mean else 'below'} the overall average ({round(overall_mean,2)})."
    )

else:
    st.info("Not enough data for grouped analysis")
st.divider()
#==================
# CORRELATION HEATMAP
# =========================
st.subheader("🔥 Correlation Analysis")

if len(numeric_cols) >= 2:

    selected_corr = st.multiselect(
        "Select columns for correlation",
        numeric_cols,
        default=numeric_cols[:4]
    )

    if len(selected_corr) >= 2:
        corr = df[selected_corr].corr()

        fig, ax = plt.subplots(figsize=(6, 5))
        cax = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)

        ax.set_xticks(range(len(corr.columns)))
        ax.set_yticks(range(len(corr.columns)))

        ax.set_xticklabels(corr.columns, rotation=45)
        ax.set_yticklabels(corr.columns)

        for i in range(len(corr)):
            for j in range(len(corr)):
                ax.text(j, i, f"{corr.iloc[i,j]:.2f}",
                        ha="center", va="center")

        fig.colorbar(cax)
        st.pyplot(fig)

        # 🔥 added insight
        strong_corr = corr.abs().unstack().sort_values(ascending=False)
        strong_corr = strong_corr[strong_corr < 1]

        if not strong_corr.empty:
            top_pair = strong_corr.index[0]
            top_value = strong_corr.iloc[0]

            if abs(top_value) < 0.1:
                strength = "no meaningful correlation"
            elif abs(top_value) < 0.5:
                strength = "weak correlation"
            else:
                strength = "strong correlation"

            st.info(
                f"{strength.capitalize()} detected between **{top_pair[0]}** and **{top_pair[1]}** "
                f"(correlation = {round(top_value,2)})."
            )
        else:
            st.info("No significant relationships found.")

    else:
        st.warning("Select at least 2 columns")
st.divider()
# =========================
# DATA PREVIEW
# =========================
st.subheader("👀 Data Preview")

rows = st.slider("Rows to preview", 5, 50, 10)
st.dataframe(df.head(rows))
st.divider()
# =========================
# EXPORT SECTION
# =========================
st.subheader("📤 Export Options")

export_format = st.selectbox("Select format", ["CSV", "Excel", "JSON"])

# -------- CSV --------
if export_format == "CSV":
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "dataset.csv", "text/csv")

# -------- EXCEL --------
elif export_format == "Excel":
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    st.download_button(
        "Download Excel",
        buffer.getvalue(),
        "dataset.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# -------- JSON --------
elif export_format == "JSON":
    json_data = df.to_json(orient="records", indent=2)

    st.download_button(
        "Download JSON",
        json_data,
        "dataset.json",
        "application/json"
    )
# =========================
# SAFE JSON FUNCTION
# =========================
def make_json_safe(obj):
    import numpy as np
    import pandas as pd

    if obj is None:
        return None

    # DataFrame → dict
    if isinstance(obj, pd.DataFrame):
        return obj.head(5).to_dict()

    # Series → list
    elif isinstance(obj, pd.Series):
        return obj.tolist()

    # Timestamp / datetime → string
    elif isinstance(obj, (pd.Timestamp, datetime)):
        return obj.isoformat()
    # numpy types → python types
    elif isinstance(obj, (np.integer,)):
        return int(obj)

    elif isinstance(obj, (np.floating,)):
        return float(obj)

    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()

    # dict → recursive
    elif isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}

    # list → recursive
    elif isinstance(obj, list):
        return [make_json_safe(i) for i in obj]

    # fallback
    else:
        return obj
st.divider()
# =========================
# TRANSFORMATION REPORT
# =========================
st.subheader("🧾 Transformation Report")

cols = st.columns([1,1,6])

with cols[0]:
    generate = st.button("Generate Report")

if generate:
    report = {
        "summary": {
            "rows": df.shape[0],
            "columns": df.shape[1],
            "missing_values": int(df.isnull().sum().sum())
        },
        "steps": st.session_state.get("history", []),
        "log": st.session_state.get("log", []),
        "generated_at": datetime.now()
    }

    safe_report = make_json_safe(report)
    report_json = json.dumps(safe_report, indent=2, default=str)

    with cols[1]:
        st.download_button(
            "Download JSON",
            report_json,
            "transformation_report.json",
            "application/json"
        )
st.divider()

# =========================
# FINAL NOTE
# =========================
st.success(
    "This dashboard provides data quality checks, statistical insights, correlation analysis, "
    "grouped analysis, and export functionality for data-driven decision making."
)