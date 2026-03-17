import streamlit as st
import pandas as pd

# ------------------ Session State ------------------

if "df" not in st.session_state:
    st.session_state["df"] = None

if "log" not in st.session_state:
    st.session_state["log"] = []

# ------------------ Title ------------------

st.title("Page A — Upload & Overview")

# ------------------ File Upload ------------------

uploaded_file = st.file_uploader(
    "Upload dataset",
    type=["csv", "xlsx", "json"],
    key="file_uploader"

)

# ------------------ Google Sheets ------------------

st.subheader("Or load from Google Sheets (optional)")

sheet_url = st.text_input("Paste Google Sheets URL")

if st.button("Load Google Sheet"):
    if sheet_url.strip() == "":
        st.warning("Please paste a Google Sheets URL.")
    else:
        try:
            if "/edit" in sheet_url:
                csv_url = sheet_url.split("/edit")[0] + "/export?format=csv"
                df = pd.read_csv(csv_url)

                st.session_state["df"] = df
                st.session_state["log"].append("Loaded from Google Sheets")
                st.success("Google Sheet loaded!")

            else:
                st.error("Invalid Google Sheets URL.")

        except Exception:
            st.error("Could not load the sheet. Make sure it is public.")

# ------------------ File Handling ------------------

if uploaded_file is not None:

    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)

        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)

        elif uploaded_file.name.endswith(".json"):
            df = pd.read_json(uploaded_file, orient="records")

        st.session_state["df"] = df
        st.session_state["log"].append("File uploaded")
        st.success("File uploaded successfully!")

    except Exception:
        st.error("Error reading file.")

# ------------------ Display Data ------------------

if st.session_state["df"] is not None:

    df = st.session_state["df"]
    df = df.convert_dtypes()

    st.subheader("Dataset Preview")
    st.dataframe(df.head())

    col1, col2 = st.columns(2)

    with col1:
        st.write("Rows:", df.shape[0])
        st.write("Columns:", df.shape[1])

    with col2:
        st.write("Duplicates:", int(df.duplicated().sum()))

    # -------- Column Types --------
    st.subheader("Column Types")

    dtype_df = pd.DataFrame({
    "Column": df.columns,
    "Type": df.dtypes.astype(str)
    })

    st.dataframe(dtype_df)

    # -------- Missing Values --------
    st.subheader("Missing Values")

    missing = df.isnull().sum()

    missing_df = pd.DataFrame({
    "Missing Count": missing,
    "Missing %": ((missing / len(df)) * 100).round(2)
    })

     
    missing_df = missing_df.sort_values(by="Missing Count", ascending=False)

    st.dataframe(missing_df)

    # -------- Categorical Summary --------
    cat_df = df.select_dtypes(include=["object", "string"])

    if cat_df.shape[1] > 0:
        st.subheader("Categorical Summary")
        st.dataframe(cat_df.describe())
    else:
        st.info("No categorical columns found.")
    # -------- Numeric Summary --------
    st.subheader("Summary Statistics")
    st.dataframe(df.describe())

# ------------------ Reset ------------------

if st.button("Reset Session"):
    st.session_state.clear()
    st.rerun()
if st.session_state.df is None:
    st.info("No dataset loaded. Please upload a file or connect Google Sheets.")