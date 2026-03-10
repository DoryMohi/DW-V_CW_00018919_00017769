import streamlit as st
import pandas as pd

st.title("Page B — Cleaning & Preparation Studio")

if "df" not in st.session_state or st.session_state["df"] is None:
    st.warning("Upload a dataset first.")
    st.stop()

df = st.session_state["df"]

st.subheader("Current Dataset")
st.dataframe(df.head())