import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("📊 Page C — Visualization Builder")

# =========================
# Dataset Selection
# =========================

st.subheader("Choose Dataset")

if "df" in st.session_state:
    df = st.session_state["df"]
    st.success("Using uploaded dataset")
else:
    dataset_choice = st.selectbox(
        "Select Dataset",
        ["Flights", "Healthcare", "Shopping"]
    )

    if dataset_choice == "Flights":
        df = pd.read_csv("sample_data/flights_dataset.csv")
    elif dataset_choice == "Healthcare":
        df = pd.read_csv("sample_data/healthcare_dataset_modified.csv")
    else:
        df = pd.read_csv("sample_data/shopping_trends_updated_model.csv")

    st.info(f"Using {dataset_choice} dataset")

# =========================
# DATA QUALITY CHECK
# =========================

missing = df.isnull().sum().sum()
if missing > 0:
    st.warning(f"Dataset contains {missing} missing values")
else:
    st.success("No missing values detected")

# =========================
# FILTER UI (SIDEBAR)
# =========================

st.sidebar.header("🔍 Filters")

filtered_df = df.copy()

if st.sidebar.button("🔄 Reset Filters"):
    st.session_state.clear()
    st.rerun()

st.sidebar.markdown("### 📊 Dataset Info")
st.sidebar.write("Rows:", df.shape[0])
st.sidebar.write("Columns:", df.shape[1])

search = st.sidebar.text_input("🔎 Search column")

columns_to_filter = [
    col for col in df.columns
    if search.lower() in col.lower()
]

# --- CATEGORICAL ---
st.sidebar.markdown("### 🏷 Categorical Filters")

for col in columns_to_filter:
    if df[col].dtype == "object":

        unique_vals = df[col].dropna().unique()

        if 2 <= len(unique_vals) <= 20:
            with st.sidebar.expander(col):

                select_all = st.checkbox(f"Select all {col}", key=f"all_{col}")

                if select_all:
                    selected = unique_vals
                else:
                    selected = st.multiselect(
                        f"Choose {col}",
                        sorted(unique_vals),
                        key=f"filter_{col}"
                    )

                if len(selected) > 0:
                    filtered_df = filtered_df[filtered_df[col].isin(selected)]

# --- NUMERIC ---
st.sidebar.markdown("### 🔢 Numeric Filters")

for col in columns_to_filter:
    if df[col].dtype in ["int64", "float64"]:

        clean_col = df[col].dropna()

        if not clean_col.empty:
            min_val = float(clean_col.min())
            max_val = float(clean_col.max())

            if min_val != max_val:
                with st.sidebar.expander(col):

                    selected_range = st.slider(
                        f"{col} range",
                        min_val,
                        max_val,
                        (min_val, max_val),
                        key=f"range_{col}"
                    )

                    filtered_df = filtered_df[
                        (filtered_df[col] >= selected_range[0]) &
                        (filtered_df[col] <= selected_range[1])
                    ]

# =========================
# SHOW FILTER RESULT
# =========================

st.subheader("Filtered Data")

col1, col2 = st.columns(2)
col1.metric("Rows After Filtering", len(filtered_df))
col2.metric("Columns", filtered_df.shape[1])

st.dataframe(filtered_df.head())

# DOWNLOAD BUTTON ✅
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    "⬇ Download Filtered Data",
    csv,
    "filtered_data.csv",
    "text/csv"
)

# STOP if empty
if filtered_df.empty:
    st.error("No data after filtering. Adjust filters.")
    st.stop()

# =========================
# PREPARE COLUMNS
# =========================

columns = [
    col for col in filtered_df.columns
    if "id" not in col.lower() and "url" not in col.lower()
]

numeric_cols = filtered_df.select_dtypes(
    include=['int64', 'float64']
).columns.tolist()

# =========================
# QUICK INSIGHT
# =========================

st.subheader("📊 Quick Insight")

if len(numeric_cols) >= 2:
    st.info(f"Suggestion: Try Scatter plot between {numeric_cols[0]} and {numeric_cols[1]}")

# =========================
# CHART SETTINGS
# =========================

chart_type = st.selectbox(
    "Select Chart Type",
    ["Scatter", "Line", "Bar", "Histogram", "Boxplot", "Pie", "Heatmap"]
)

if chart_type in ["Scatter", "Line"]:
    x_col = st.selectbox("Select X-axis (numeric)", numeric_cols)
else:
    x_col = st.selectbox("Select X-axis", columns)

y_col = None
if chart_type not in ["Histogram", "Pie", "Heatmap"]:
    y_options = [col for col in numeric_cols if col != x_col]
    y_col = st.selectbox("Select Y-axis", y_options)

top_n = None
if chart_type == "Bar":
    top_n = st.slider("Top N categories", 5, 20, 10)

# =========================
# GENERATE CHART
# =========================

if st.button("Generate Chart"):

    if len(filtered_df) < 2:
        st.warning("Not enough data to plot")
        st.stop()

    # PERFORMANCE SAFE
    plot_df = filtered_df.copy()
    if len(plot_df) > 5000:
        st.warning("Large dataset, sampling for performance")
        plot_df = plot_df.sample(5000)

    with st.spinner("Generating chart..."):

        fig, ax = plt.subplots(figsize=(7,5))

        try:
            if chart_type == "Scatter":
                data = plot_df[[x_col, y_col]].dropna()
                ax.scatter(data[x_col], data[y_col], alpha=0.7)
                ax.grid(True)

            elif chart_type == "Line":
                data = plot_df[[x_col, y_col]].dropna().sort_values(by=x_col)
                ax.plot(data[x_col], data[y_col], marker='o')
                ax.grid(True)

            elif chart_type == "Bar":
                data = plot_df[x_col].value_counts().head(top_n)
                ax.bar(data.index.astype(str), data.values)
                plt.xticks(rotation=45)

            elif chart_type == "Histogram":
                ax.hist(plot_df[x_col].dropna())

            elif chart_type == "Boxplot":
                ax.boxplot(plot_df[y_col].dropna())

            elif chart_type == "Pie":
                data = plot_df[x_col].value_counts().head(10)
                ax.pie(data, labels=data.index, autopct='%1.1f%%')

            elif chart_type == "Heatmap":
                corr = plot_df[numeric_cols].corr()
                cax = ax.matshow(corr)
                fig.colorbar(cax)

                ax.set_xticks(range(len(corr.columns)))
                ax.set_yticks(range(len(corr.columns)))
                ax.set_xticklabels(corr.columns, rotation=90)
                ax.set_yticklabels(corr.columns)

        except Exception as e:
            st.error(f"Error: {e}")

        ax.set_title(chart_type)

        if x_col:
            ax.set_xlabel(x_col)
        if y_col:
            ax.set_ylabel(y_col)

        st.pyplot(fig)