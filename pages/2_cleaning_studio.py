import streamlit as st
import pandas as pd
import numpy as np

from utils import add_log
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

if st.session_state["log"]:
    for i, entry in enumerate(st.session_state["log"], 1):
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