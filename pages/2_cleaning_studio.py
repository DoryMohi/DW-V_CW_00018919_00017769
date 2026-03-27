import streamlit as st
import pandas as pd
import numpy as np

from utils import add_log

if "history" not in st.session_state:
    st.session_state["history"] = []
# ------------------ STYLE ------------------
st.markdown("""
<style>
.section { margin-top: 30px; }

.card {
    background: #F9FAFB;
    padding: 18px;
    border-radius: 10px;
    border: 1px solid #E5E7EB;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

st.title("Page B — Cleaning & Preparation Studio")


df = st.session_state.get("df")

if df is None:
    st.warning("⚠️ Upload a dataset first from Page A.")
    st.stop()

if "log" not in st.session_state:
    st.session_state["log"] = []

df = df.copy().convert_dtypes()
st.session_state["df"] = df

# ------------------ Dataset Control ------------------
st.markdown("## Dataset Control")

if "original_df" in st.session_state:
    if st.button("🔄 Reset to Original Data", key="reset_btn"):
        original = st.session_state["original_df"].copy()
        st.session_state["df"] = original

        add_log(
            operation="Reset",
            columns="All",
            method="-",
            action="Restore original dataset",
            affected=len(original),
            details=f"{original.shape[1]} columns"
        )

        st.success("Dataset restored.")
        st.rerun()
st.session_state["df"] = df
# ------------------ CALL SECTIONS ------------------
from cleaning_core import (
    missing_section,
    duplicates_section,
    types_section,
    categorical_section,
    outliers_section
)
from feature_engineering import feature_engineering_section

missing_section(df, add_log)
df = st.session_state["df"]

duplicates_section(df, add_log)
df = st.session_state["df"]

types_section(df, add_log)
df = st.session_state["df"]

categorical_section(df, add_log)
df = st.session_state["df"]

outliers_section(df, add_log)
df = st.session_state["df"]

feature_engineering_section(df, add_log)
df = st.session_state["df"]

# ----------- Split columns ----------------
st.subheader("Split Interval Columns")

if "split_columns_done" not in st.session_state:
    st.session_state["split_columns_done"] = []

# ✅ allow BOTH numeric intervals + date ranges
interval_cols = [
    col for col in df.columns
    if df[col].astype(str).str.contains(r"\(.*?,.*?\]|\d{2}\.\d{2}\.\d{4}-\d{2}\.\d{2}\.\d{4}").any()
]

if not interval_cols:
    st.info("No interval columns available to split.")
else:
    interval_col = st.selectbox(
        "Select interval column",
        interval_cols,
        key="interval_col_select"
    )

    prefix = st.text_input("New column prefix (e.g., Age_bin)")

    already_done = interval_col in st.session_state["split_columns_done"]

    if already_done:
        st.info(f"'{interval_col}' already split.")

    if st.button("Split Column", disabled=already_done):
        st.session_state["history"].append(df.copy())

        if not prefix.strip():
            st.warning("Enter a valid prefix.")
            st.stop()

        df_copy = df.copy()

        try:
            col_data = df_copy[interval_col].astype(str)

            # -------- DETECT FORMAT --------
            is_date_range = col_data.str.contains(
                r'\d{2}\.\d{2}\.\d{4}-\d{2}\.\d{2}\.\d{4}'
            ).any()

            # -------- DATE SPLIT --------
            if is_date_range:
                extracted = col_data.str.extract(
                    r'(\d{2}\.\d{2}\.\d{4})-(\d{2}\.\d{2}\.\d{4})'
                )

                if extracted.isnull().all().all():
                    st.error("Invalid date range format.")
                    st.stop()

                start_col = f"{prefix}_start"
                end_col = f"{prefix}_end"

                df_copy[start_col] = pd.to_datetime(
                    extracted[0], format="%d.%m.%Y"
                )
                df_copy[end_col] = pd.to_datetime(
                    extracted[1], format="%d.%m.%Y"
                )

                df_copy[f"{prefix}_duration_days"] = (
                    df_copy[end_col] - df_copy[start_col]
                ).dt.days

                preview_cols = [start_col, end_col]

            # -------- NUMERIC SPLIT --------
            else:
                extracted = col_data.str.extract(
                    r'\(?([\d\.]+)\s*[,/;\-]\s*([\d\.]+)\]?'
                )

                if extracted.isnull().all().all():
                    st.error("Column is not a valid interval format.")
                    st.stop()

                extracted = extracted.astype(float)

                lower_col = f"{prefix}_lower"
                upper_col = f"{prefix}_upper"

                df_copy[lower_col] = extracted[0]
                df_copy[upper_col] = extracted[1]

                preview_cols = [lower_col, upper_col]

            # -------- SAVE --------
            st.session_state["df"] = df_copy
            st.session_state["split_columns_done"].append(interval_col)

            st.success("Column split successfully")

            add_log(
                operation="Split Column",
                columns=interval_col,
                method="Regex extraction",
                action="Split into new columns",
                affected=len(df_copy),
                details=", ".join(preview_cols)
            )

            st.dataframe(df_copy[preview_cols].head())

        except Exception as e:
            st.error(f"Error: {e}")

st.markdown("---")
# ------------------ Download Cleaned Dataset ------------------
df = st.session_state["df"]
st.subheader("Download Cleaned Dataset")

format = st.selectbox("Select format", ["CSV", "Excel", "JSON"])

if format == "CSV":
    data = df.to_csv(index=False)
    file_name = "cleaned_dataset.csv"
    mime = "text/csv"

elif format == "Excel":
    from io import BytesIO
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    data = buffer
    file_name = "cleaned_dataset.xlsx"
    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

elif format == "JSON":
    data = df.to_json(orient="records")
    file_name = "cleaned_dataset.json"
    mime = "application/json"

if st.download_button(
    label="Download", 
    data=data, 
    file_name=file_name, 
    mime=mime
):
    add_log(
        operation="Download",
        columns="All",
        method=f"{format} export",
        action="Dataset exported",
        affected=len(df),
        details=f"{df.shape[0]} rows, {df.shape[1]} columns"
    )
st.markdown("---")
st.markdown("## Transformation Log")
col1, col2 = st.columns([1, 2])

with col1:
    undo_clicked = st.button("↩️ Undo Last Step")

    if undo_clicked:
        if st.session_state["history"]:
            st.session_state["df"] = st.session_state["history"].pop()

            if st.session_state["log"]:
                last = st.session_state["log"].pop()
                st.session_state["undo_msg"] = f"Reverted: {last.get('operation', 'Last action')}"
            else:
                st.session_state["undo_msg"] = "Last action undone"

            st.rerun()
        else:
            st.warning("No history to undo")

with col2:
    if "undo_msg" in st.session_state:
        st.info(st.session_state["undo_msg"])
        del st.session_state["undo_msg"]  

logs = st.session_state.get("log", [])

for entry in logs:
    if not isinstance(entry, dict):
        st.error(f"Invalid log entry detected: {entry}")
if logs:
    st.caption(f"{len(logs)} total operations (Recent to old)")

    # ✅ show only last 10
    recent_logs = logs[-10:]

    for i, entry in enumerate(reversed(recent_logs), 1):
        if isinstance(entry, dict):
            st.markdown(f"""
    **{i}. {entry.get('operation', '-') }**

    - Column: `{entry.get('columns', '-')}`
    - Method: `{entry.get('method', '-')}`
    - Action: `{entry.get('action', '-')}`
    - Details: `{entry.get('details', '-')}`
    - Affected: `{entry.get('affected', '-')}`
    """)
        else:
            st.warning(f"{i}. Invalid log entry: {entry}")

    # ✅ full history (optional)
    with st.expander("Show full log history"):
        for i, entry in enumerate(reversed(logs), 1):
            st.markdown(f"""
**{i}. {entry['operation']}**

- Column: `{entry['columns']}`
- Method: `{entry['method']}`
- Action: `{entry['action']}`
- Details: `{entry.get('details', '-')}`
- Affected: `{entry['affected']}`
""")

else:
    st.info("No transformations yet.")