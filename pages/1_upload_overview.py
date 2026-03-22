import streamlit as st
import pandas as pd

# ------------------ STYLE ------------------
st.markdown("""
<style>

.block-container {
    padding-top: 2rem;
}

/* Section titles */
.section-title {
    font-size: 22px;
    font-weight: 600;
    margin-top: 30px;
    margin-bottom: 10px;
}

/* Metric cards */
.metric-card {
    background: #F9FAFB;
    padding: 18px;
    border-radius: 10px;
    border: 1px solid #E5E7EB;
    text-align: center;
}

.metric-value {
    font-size: 26px;
    font-weight: 600;
    color: #111827;
}

.metric-label {
    font-size: 13px;
    color: #6B7280;
}

/* Tables */
.table-card {
    margin-top: 10px;
}

</style>
""", unsafe_allow_html=True)

# ------------------ CACHE (REQUIRED) ------------------
@st.cache_data
def load_csv(file):
    return pd.read_csv(file)

@st.cache_data
def load_excel(file):
    return pd.read_excel(file)

@st.cache_data
def load_json(file):
    return pd.read_json(file, orient="records")

@st.cache_data
def load_sheet(url):
    return pd.read_csv(url)


# ------------------ SESSION STATE ------------------
if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0

if "df" not in st.session_state:
    st.session_state["df"] = None

if "log" not in st.session_state:
    st.session_state["log"] = []

if "source" not in st.session_state:
    st.session_state["source"] = None

if "last_uploaded" not in st.session_state:
    st.session_state["last_uploaded"] = None

# ------------------ TITLE ------------------
st.markdown("""
<h1 style='font-size:40px;'>Upload Dataset</h1>
<p style='color:#6B7280; font-size:16px;'>
Upload your data or connect a source to begin analysis.
</p>
""", unsafe_allow_html=True)


# ------------------ FUNCTIONS ------------------
def log_upload(name, df):
    if st.session_state["last_uploaded"] != name:
        rows, cols = df.shape

        st.session_state["log"].append(
            f"<b>Upload </b> → {name}  •  <b>Rows:</b> {rows}  •  <b>Columns:</b> {cols}  •  <b>Sample Columns:</b> {list(df.columns[:3])}..."
        )

        st.session_state["last_uploaded"] = name

    if len(st.session_state["log"]) > 20:
        st.session_state["log"] = st.session_state["log"][-20:]

def load_file(uploaded_file):
    try:
        if uploaded_file.name.endswith(".csv"):
            df = load_csv(uploaded_file)

        elif uploaded_file.name.endswith(".xlsx"):
            df = load_excel(uploaded_file)

        elif uploaded_file.name.endswith(".json"):
            df = load_json(uploaded_file)

        else:
            st.error("Unsupported file type.")
            return

        if df.empty:
            st.error("Uploaded file is empty.")
            return

        st.session_state["df"] = df
        st.session_state["original_df"] = df.copy()
        st.session_state["source"] = uploaded_file.name

        log_upload(uploaded_file.name, df)

        st.success(f"✔ File '{uploaded_file.name}' loaded successfully")
        st.rerun()

    except Exception as e:
        st.error(f"Error reading file: {e}")


def load_google_sheet(sheet_url):
    try:
        if sheet_url.strip() == "":
            st.warning("Please paste a URL.")
            return

        if "/edit" not in sheet_url:
            st.error("Invalid Google Sheets link.")
            return

        csv_url = sheet_url.split("/edit")[0] + "/export?format=csv"
        df = load_sheet(csv_url)

        if df.empty:
            st.error("Google Sheet is empty.")
            return

        st.session_state["df"] = df
        st.session_state["original_df"] = df.copy()
        st.session_state["source"] = "Google Sheets"

        log_upload("Google Sheets", df)

        st.success("✔ Google Sheet loaded successfully")
        st.rerun()

    except Exception as e:
        st.error(f"Failed to load sheet: {e}")

# ------------------ UI LOGIC ------------------
df = st.session_state.get("df")

# ------------------ NO DATA ------------------
if df is None:
    with st.expander("Upload or connect dataset", expanded=True):

        uploaded_file = st.file_uploader(
            "Upload File",
            type=["csv", "xlsx", "json"],
            key=f"uploader_{st.session_state['uploader_key']}"
        )

        if uploaded_file is not None:
            load_file(uploaded_file)

        st.markdown("---")

        st.subheader("Load from Google Sheets")
        sheet_url = st.text_input("Google Sheets URL")

        if st.button("Load Sheet"):
            load_google_sheet(sheet_url)


# ------------------ DATA LOADED ------------------
else:

    df = df.convert_dtypes()

    rows, cols = df.shape
    missing = int(df.isna().sum().sum())
    duplicates = int(df.duplicated().sum())
    source = st.session_state.get("source", "Unknown")

    # -------- OVERVIEW --------
    st.markdown('<div class="section-title">Dataset Overview</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    c1.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{rows}</div>
        <div class="metric-label">Rows</div>
    </div>
    """, unsafe_allow_html=True)

    c2.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{cols}</div>
        <div class="metric-label">Columns</div>
    </div>
    """, unsafe_allow_html=True)

    c3.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{missing}</div>
        <div class="metric-label">Missing</div>
    </div>
    """, unsafe_allow_html=True)

    c4.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{duplicates}</div>
        <div class="metric-label">Duplicates</div>
    </div>
    """, unsafe_allow_html=True)

    st.caption(f"Source: {source}")

    # -------- PREVIEW --------
    st.markdown('<div class="section-title">Preview</div>', unsafe_allow_html=True)
    st.dataframe(df.head(10), use_container_width=True)

    # -------- ACTIONS --------
    colA, colB = st.columns([1, 3])

    with colA:
        if st.button("Remove dataset ⚠️", type="primary"):
            st.session_state["df"] = None
            st.session_state["uploader_key"] += 1
            st.rerun()

    # -------- REPLACE --------
    with st.expander("Upload new dataset"):

        uploaded_file = st.file_uploader(
            "Upload new file",
            type=["csv", "xlsx", "json"],
            key=f"replace_{st.session_state['uploader_key']}"
        )

        if uploaded_file is not None:
            load_file(uploaded_file)

        st.markdown("---")

        sheet_url = st.text_input("Google Sheets URL", key="replace_sheet")

        if st.button("Load Sheet", key="replace_btn"):
            load_google_sheet(sheet_url)

    # -------- COLUMN TYPES --------
    st.markdown('<div class="section-title">Column Types</div>', unsafe_allow_html=True)

    dtype_df = pd.DataFrame({
        "Column": df.columns,
        "Type": df.dtypes.astype(str)
    })

    st.dataframe(dtype_df, use_container_width=True)

    # -------- MISSING VALUES --------
    st.markdown('<div class="section-title">Missing Values</div>', unsafe_allow_html=True)

    missing_series = df.isnull().sum()

    missing_df = pd.DataFrame({
        "Missing Count": missing_series,
        "Missing %": ((missing_series / len(df)) * 100).round(2)
    }).sort_values(by="Missing Count", ascending=False)

    st.dataframe(missing_df, use_container_width=True)

    # -------- CATEGORICAL --------
    cat_df = df.select_dtypes(include=["object", "string"])

    if not cat_df.empty:
        st.markdown('<div class="section-title">Categorical Summary</div>', unsafe_allow_html=True)
        st.dataframe(cat_df.describe(), use_container_width=True)

    # -------- NUMERIC --------
    num_df = df.select_dtypes(include="number")

    if not num_df.empty:
        st.markdown('<div class="section-title">Summary Statistics</div>', unsafe_allow_html=True)
        st.dataframe(num_df.describe(), use_container_width=True)

    # -------- LOG --------
    st.markdown('<div class="section-title">Transformation Log</div>', unsafe_allow_html=True)

    if st.session_state["log"]:
        for i, step in enumerate(st.session_state["log"], 1):
            st.markdown(f"""
            <div style="
                background:#F9FAFB;
                padding:10px 14px;
                border-radius:8px;
                border:1px solid #E5E7EB;
                margin-bottom:6px;
                font-size:14px;
            ">
                <b>{i}.</b> {step}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("No transformations yet.")


# ------------------ RESET ------------------
if st.button("Reset Session", type="primary"):
    st.session_state.clear()
    st.session_state["uploader_key"] = 0
    st.rerun()