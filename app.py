import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="AI Data Wrangler",
    layout="wide"
)

st.title("AI-Assisted Data Wrangler & Visualizer")

# Initialize session state
if "df" not in st.session_state:
    st.session_state["df"] = None

if "log" not in st.session_state:
    st.session_state["log"] = []

st.write("Use the sidebar to navigate between pages.")