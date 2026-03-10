import streamlit as st
import pandas as pd

if "df" not in st.session_state:
    st.session_state["df"] = None

if "log" not in st.session_state:
    st.session_state["log"] = []
    
st.title("Page A — Upload & Overview")

uploaded_file = st.file_uploader(
    "Upload dataset",
    type=["csv", "xlsx", "json"]
)

if uploaded_file is not None:

    # Detect file type
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)

    elif uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)

    elif uploaded_file.name.endswith(".json"):
        df = pd.read_json(uploaded_file)

    st.session_state.df = df

if st.session_state.df is not None:

    df = st.session_state.df

    st.subheader("Dataset Preview")
    st.dataframe(df.head())

    col1, col2 = st.columns(2)

    with col1:
        st.write("Rows:", df.shape[0])
        st.write("Columns:", df.shape[1])

    with col2:
        st.write("Duplicates:", df.duplicated().sum())

    st.subheader("Column Types")
    st.write(df.dtypes)

    st.subheader("Missing Values")
    missing = df.isnull().sum()
    st.dataframe(missing)

    st.subheader("Summary Statistics")
    st.dataframe(df.describe())

if st.button("Reset Session"):
    st.session_state.df = None
    st.session_state.log = []