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