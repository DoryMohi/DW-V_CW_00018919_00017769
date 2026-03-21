import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="AI Data Wrangler",
    layout="wide"
)

# ------------------ STYLE ------------------
st.markdown("""
<style>

/* NEW CLEAN CARDS */
.clean-card {
    background: #ffffff;
    padding: 22px;
    border-radius: 12px;

    border: 1px solid #E5E7EB;
    border-left: 4px solid #22C55E;

    transition: all 0.2s ease;
    height: 100%;
    cursor: pointer;

}

.clean-card:hover {
    transform: translateY(-3px);
    box-shadow: 0px 8px 20px rgba(0,0,0,0.06);
    border-left: 4px solid #22C55E;
}

/* title */
.clean-card h3 {
    color: #111827;
    font-size: 20px;
    font-weight: 700; /* was 600 */
    margin-bottom: 8px;
}

.clean-card p {
    color: #6B7280;
    font-size: 14px;
    line-height: 1.5;
}

</style>
""", unsafe_allow_html=True)
# ------------------ STATE ------------------
if "df" not in st.session_state:
    st.session_state["df"] = None

if "log" not in st.session_state:
    st.session_state["log"] = []

# ------------------ HERO ------------------
st.markdown("""
<h1 style='font-size: 44px; margin-bottom: 5px;'>AI Data Wrangler</h1>
<p style='color: #6B7280; font-size:16px;'>
Clean, transform, and visualize your data — without the mess.
</p>
""", unsafe_allow_html=True)
st.divider()

# ------------------ FEATURES ------------------
col1, col2, col3 = st.columns(3, gap="large")

with col1:
    st.markdown("""
    <div class="clean-card">
        <h3>Data Cleaning</h3>
        <p>Handle missing values, duplicates, and inconsistencies.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="clean-card">
        <h3>Transformation</h3>
        <p>Convert types, encode features, and engineer new columns.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="clean-card">
        <h3>Visualization</h3>
        <p>Explore patterns with interactive charts and dashboards.</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ------------------ STATUS ------------------
st.markdown("### 📂 Dataset Status")

df = st.session_state.get("df")

if df is None:
    st.markdown("""
    <div style="
        background-color:#F0F7FF;
        padding:16px;
        border-radius:10px;
        border:1px solid #D6E4FF;
        color:#1E40AF;
        font-size:15px;">
        No dataset uploaded yet. Go to <b>Upload Overview</b> to get started.
    </div>
    """, unsafe_allow_html=True)

else:
    rows, cols = df.shape
    missing = int(df.isna().sum().sum())

    st.markdown(f"""
    <div style="
        background-color:#ECFDF5;
        padding:18px;
        border-radius:12px;
        border:1px solid #A7F3D0;
        color:#065F46;
        font-size:15px;
        line-height:1.7;
        max-width:800px;
    ">
        <b style="font-size:16px;">Dataset loaded successfully</b>
        <div style="margin-top:10px;">
            Rows: <b>{rows}</b><br>
            Columns: <b>{cols}</b><br>
            Missing values: <b>{missing}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)