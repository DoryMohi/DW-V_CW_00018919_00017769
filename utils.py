import streamlit as st
import pandas as pd

def add_log(operation, columns, method, action, affected, details="-"):
    if "log" not in st.session_state:
        st.session_state["log"] = []

    st.session_state["log"].append({
        "operation": str(operation),
        "columns": str(columns),
        "method": str(method),
        "action": str(action),
        "affected": int(affected),
        "details": str(details)
    })

    if len(st.session_state["log"]) > 20:
        st.session_state["log"] = st.session_state["log"][-20:]

def detect_id_columns(df):
    id_keywords = ["id", "customer", "order", "user"]

    id_cols = []

    for col in df.columns:
        col_lower = col.lower()

        # 1. Name-based detection
        if any(keyword in col_lower for keyword in id_keywords):
            id_cols.append(col)
            continue

        # 2. Value-based detection (unique = likely ID)
        if df[col].nunique(dropna=True) == len(df):
            id_cols.append(col)

    return list(set(id_cols))