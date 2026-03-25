import streamlit as st
import pandas as pd

def add_log(operation, columns="All", method="-", action="-", affected=None, details=""):
    if "log" not in st.session_state:
        st.session_state["log"] = []

    st.session_state["log"].append({
        "time": pd.Timestamp.now().strftime("%H:%M:%S"),
        "operation": operation,
        "columns": columns,
        "method": method,
        "action": action,
        "affected": affected,
        "details": details
    })

    if len(st.session_state["log"]) > 20:
        st.session_state["log"] = st.session_state["log"][-20:]