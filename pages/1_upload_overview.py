import streamlit as st
import pandas as pd

# ------------------ SESSION STATE ------------------

if "df" not in st.session_state:
    st.session_state["df"] = None

if "log" not in st.session_state:
    st.session_state["log"] = []

if "source" not in st.session_state:
    st.session_state["source"] = None


# ------------------ TITLE ------------------

st.title("Page A — Upload & Overview")


# ------------------ FILE UPLOAD ------------------

uploaded_file = st.file_uploader("Upload File", type=["csv", "xlsx", "json"])

if uploaded_file is not None:
    
    try:
        df = None  # ✅ IMPORTANT SAFETY LINE

        # ---- Read file safely ----
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)

        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)

        elif uploaded_file.name.endswith(".json"):
            df = pd.read_json(uploaded_file, orient="records")

        else:
            st.error("Unsupported file type.")

        # ---- Validation ----
        if df is not None:
            if df.empty:
                st.error("Uploaded file is empty.")
            else:
                st.session_state["df"] = df
                st.session_state["source"] = uploaded_file.name
                st.session_state["log"].append(f"Uploaded file: {uploaded_file.name}")

                st.success(f"File '{uploaded_file.name}' loaded successfully!")

    except Exception as e:
        st.error(f"Error reading file: {e}")


# ------------------ GOOGLE SHEETS ------------------

st.subheader("Or load from Google Sheets")

sheet_url = st.text_input("Paste Google Sheets URL")

if st.button("Load Google Sheet"):
    try:
        if sheet_url.strip() == "":
            st.warning("Please paste a URL.")

        elif "/edit" not in sheet_url:
            st.error("Invalid Google Sheets link.")

        else:
            csv_url = sheet_url.split("/edit")[0] + "/export?format=csv"
            df = pd.read_csv(csv_url)

            if df.empty:
                st.error("Google Sheet is empty.")
            else:
                st.session_state["df"] = df
                st.session_state["source"] = "Google Sheets"
                st.session_state["log"].append("Loaded from Google Sheets")

                st.success("Google Sheet loaded successfully!")

    except Exception as e:
        st.error(f"Failed to load sheet: {e}")


# ------------------ DISPLAY DATA ------------------

df = st.session_state.get("df")

df = st.session_state.get("df")

if df is not None:
    df = df.convert_dtypes()

    st.subheader("Dataset Preview")
    st.dataframe(df.head())

    # ---- Basic Info ----
    col1, col2 = st.columns(2)

    with col1:
        st.write("Rows:", df.shape[0])
        st.write("Columns:", df.shape[1])

    with col2:
        st.write("Duplicates:", int(df.duplicated().sum()))
        st.write("Source:", st.session_state.get("source"))

    # ---- Column Types ----
    st.subheader("Column Types")

    dtype_df = pd.DataFrame({
        "Column": df.columns,
        "Type": df.dtypes.astype(str)
    })

    st.dataframe(dtype_df)

    # ---- Missing Values ----
    st.subheader("Missing Values")

    missing = df.isnull().sum()

    missing_df = pd.DataFrame({
        "Missing Count": missing,
        "Missing %": ((missing / len(df)) * 100).round(2)
    }).sort_values(by="Missing Count", ascending=False)

    st.dataframe(missing_df)

    # ---- Categorical ----
    cat_df = df.select_dtypes(include=["object", "string"])

    if not cat_df.empty:
        st.subheader("Categorical Summary")
        st.dataframe(cat_df.describe())
    else:
        st.info("No categorical columns found.")

    # ---- Numeric ----
    num_df = df.select_dtypes(include="number")

    if not num_df.empty:
        st.subheader("Summary Statistics")
        st.dataframe(num_df.describe())
    else:
        st.info("No numeric columns found.")

else:
    st.info("No dataset loaded. Please upload a file.")


# ------------------ RESET ------------------

if st.button("Reset Session"):
    st.session_state.clear()
    st.rerun()

# ------------------ EMPTY STATE ------------------

if st.session_state.get("df") is None:
    st.info("No dataset loaded. Please upload a file or connect Google Sheets.")
    