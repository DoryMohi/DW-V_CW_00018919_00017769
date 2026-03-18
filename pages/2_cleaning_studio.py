import streamlit as st
import pandas as pd

st.title("Page B — Cleaning & Preparation Studio")

df = st.session_state.get("df")

if df is None:
    st.warning("Upload data first in Page A.")
    st.stop()

# ------------------ MISSING SUMMARY ------------------

st.subheader("Missing Values Summary")

missing = df.isnull().sum()
missing_df = pd.DataFrame({
    "Missing Count": missing,
    "Missing %": ((missing / len(df)) * 100).round(2)
}).sort_values(by="Missing Count", ascending=False)

st.dataframe(missing_df)

# ------------------ SELECT COLUMN ------------------

st.subheader("Handle Missing Values")

col = st.selectbox("Select column", df.columns)
is_numeric = pd.api.types.is_numeric_dtype(df[col])

if is_numeric:
    actions = [
        "Drop rows",
        "Fill with mean",
        "Fill with median",
        "Fill with mode",
        "Fill with constant",
        "Forward fill",
        "Backward fill"
    ]
else:
    actions = [
        "Drop rows",
        "Fill with mode",
        "Fill with constant",
        "Forward fill",
        "Backward fill"
    ]


action = st.selectbox("Choose action", [
    "Drop rows",
    "Fill with mean",
    "Fill with median",
    "Fill with mode",
    "Fill with constant",
    "Forward fill",
    "Backward fill"
])

# ------------------ BEFORE INFO ------------------

before_rows = len(df)

# ------------------ APPLY BUTTON ------------------

if st.button("Apply Missing Value Operation"):

    df_copy = df.copy()

    try:
        if action in ["Fill with mean", "Fill with median"] and not is_numeric:
            st.error("Only numeric columns allowed.")
            st.stop() 
        if action == "Drop rows":
            df_copy = df_copy.dropna(subset=[col])

        elif action == "Fill with mean":
            df_copy[col] = df_copy[col].fillna(df_copy[col].mean())

        elif action == "Fill with median":
            df_copy[col] = df_copy[col].fillna(df_copy[col].median())

        elif action == "Fill with mode":
            df_copy[col] = df_copy[col].fillna(df_copy[col].mode()[0])

        elif action == "Fill with constant":
            value = st.text_input("Enter value")
            if value != "":
                df_copy[col] = df_copy[col].fillna(value)
            else:
                st.warning("Enter a value first.")
                st.stop()

        elif action == "Forward fill":
            df_copy[col] = df_copy[col].fillna(method="ffill")

        elif action == "Backward fill":
            df_copy[col] = df_copy[col].fillna(method="bfill")

        # SAVE
        st.session_state["df"] = df_copy

        # LOG
        st.session_state["log"].append(f"{action} applied on {col}")

        # AFTER INFO
        after_rows = len(df_copy)

        st.success("Operation applied!")

        #st.write("Before rows:", before_rows)
        #st.write("After rows:", after_rows)
        st.write("Missing before:", df[col].isnull().sum())
        st.write("Missing after:", df_copy[col].isnull().sum())

    except Exception as e:
        st.error(f"Error: {e}")