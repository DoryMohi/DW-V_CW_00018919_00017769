import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
from utils import detect_id_columns

st.title("Page C — Visualization Builder")

# =========================
# LOAD CLEANED DATA
# =========================
if "df" not in st.session_state or st.session_state["df"] is None:
    st.error("No dataset available. Please upload and clean data first.")
    st.stop()

df = st.session_state["df"].copy()

st.success("Using current dataset (cleaned if applied)")
st.caption(f"{df.shape[0]} rows × {df.shape[1]} columns")

# =========================
# DATA TYPES
# =========================
ignore_cols = detect_id_columns(df)

numeric_cols = [
    col for col in df.select_dtypes(include=["int64", "float64"]).columns
    if col not in ignore_cols
]

categorical_cols = [
    col for col in df.select_dtypes(include=["object", "category", "string"]).columns
    if col not in ignore_cols
]
datetime_cols = df.select_dtypes(include=["datetime64[ns]"]).columns.tolist()
important_cats = [
    col for col in categorical_cols
    if df[col].nunique() <= 20
][:10]

# =========================
# FILTERS (SIDEBAR)
# =========================
st.sidebar.header("🔍 Filters")

filtered_df = df.copy()

# -------- CATEGORICAL --------
with st.sidebar.expander("🏷 Categorical Filters", expanded=False):
    for col in important_cats:
        selected = st.multiselect(
            col,
            sorted(df[col].dropna().unique()),
            key=f"cat_{col}"
        )

        if selected:
            filtered_df = filtered_df[filtered_df[col].isin(selected)]

# -------- NUMERIC --------
with st.sidebar.expander("🔢 Numeric Filters", expanded=False):
    for col in numeric_cols:
        clean_col = df[col].dropna()
        if clean_col.empty:
            continue

        min_val = float(clean_col.quantile(0.01))
        max_val = float(clean_col.quantile(0.99))

        if min_val == max_val:
            continue

        selected = st.slider(
            col,
            min_val,
            max_val,
            (min_val, max_val),
            key=f"num_{col}"
        )

        # Only filter if user actually changed range
        if selected != (min_val, max_val):
            filtered_df = filtered_df[
                (filtered_df[col] >= selected[0]) &
                (filtered_df[col] <= selected[1])
            ]
# =========================
# PREVIEW
# =========================
st.subheader("Filtered Data")

col1, col2 = st.columns(2)
col1.metric("Rows", len(filtered_df))
col2.metric("Columns", filtered_df.shape[1])

st.dataframe(filtered_df.head())

if filtered_df.empty:
    st.error("No data after filtering.")
    st.stop()



# =========================
# CHART CONFIG
# =========================
st.subheader("📊 Build Chart")

chart_type = st.selectbox(
    "Chart Type",
    ["Histogram", "Boxplot", "Scatter", "Line", "Bar", "Heatmap"]
)

x_col = y_col = color_col = agg = None
top_n = None

# =========================
# DYNAMIC UI
# =========================

if chart_type == "Histogram":
    x_col = st.selectbox("Numeric column", numeric_cols)

elif chart_type == "Boxplot":
    y_col = st.selectbox("Numeric column", numeric_cols)
    valid_group_cols = [
    col for col in categorical_cols
    if 2 <= df[col].nunique() <= 10
    ]

    group_col = st.selectbox(
        "Group by (optional)",
        ["None"] + valid_group_cols
    )

elif chart_type == "Scatter":
    x_col = st.selectbox("X (numeric)", numeric_cols)
    y_col = st.selectbox("Y (numeric)", [c for c in numeric_cols if c != x_col])
    color_mode = st.radio("Color mode", ["Single color", "By category"])

    if color_mode == "Single color":
        color_value = st.color_picker("Pick a color", "#1f77b4")
        color_col = None
    else:
        color_col = st.selectbox("Color by category", categorical_cols)
        color_value = None
        

elif chart_type == "Line":
    
    st.info("Use 'Date Filter' function on the on the sidebar for improving readability (if needed)")
    if not datetime_cols:
        st.warning("No datetime column available for line chart.")
        st.stop()

    x_col = st.selectbox("Time column", datetime_cols)
    
    with st.sidebar.expander("📅 Date Filter", expanded=False):
        if datetime_cols:
            date_col = st.selectbox("Date column", datetime_cols)

            df[date_col] = pd.to_datetime(df[date_col])

            min_date = df[date_col].min().to_pydatetime()
            max_date = df[date_col].max().to_pydatetime()

            date_range = st.slider(
                "Select date range",
                min_value=min_date,
                max_value=max_date,
                value=(min_date, max_date)
            )

            filtered_df = filtered_df[
                (filtered_df[date_col] >= pd.to_datetime(date_range[0])) &
                (filtered_df[date_col] <= pd.to_datetime(date_range[1]))
            ]
    y_col = st.selectbox("Value", numeric_cols)

    group_col = st.selectbox(
        "Group by (optional)",
        ["None"] + categorical_cols
    )

elif chart_type == "Bar":
    x_col = st.selectbox("Category", categorical_cols)

    agg = st.selectbox("Aggregation", ["count", "sum", "mean", "median"])

    if agg != "count":
        y_col = st.selectbox("Value", numeric_cols)
    else:
        y_col = None

    color_col = st.selectbox(
        "Group by (optional)",
        ["None"] + categorical_cols
    )

    # safe top_n
    if color_col != "None":
        max_groups = df[color_col].nunique()
    else:
        max_groups = df[x_col].nunique()

    if max_groups > 2:
        top_n = st.slider("Top N categories", 2, max_groups, min(5, max_groups))
    else:
        top_n = max_groups
        
    st.caption("Top N categories will be updated based on the filtered data.")

elif chart_type == "Heatmap":
    selected_cols = st.multiselect(
        "Select numeric columns",
        numeric_cols,
        default=numeric_cols[:5]  # NOT just 2–3
    )

    if len(selected_cols) < 2:
        st.warning("Select at least 2 columns.")

# =========================
# GENERATE CHART
# =========================
if st.button("Generate Chart"):

    fig, ax = plt.subplots(figsize=(7, 5))

    try:
        if chart_type == "Histogram":
            data = filtered_df[x_col].dropna()

            # better bins
            bins = min(20, max(8, int(len(data) ** 0.5)))

            counts, bins, patches = ax.hist(
                data, 
                bins=bins,
                color= "#2A6F97",
                edgecolor="white",
                alpha=0.85
            )
            for patch in patches:
                patch.set_facecolor("#2A6F97")
                patch.set_alpha(0.85)

            # clean look
            ax.grid(True, linestyle="--", alpha=0.3)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

            ax.set_title(f"Distribution of {x_col}")
            ax.set_xlabel(x_col)
            ax.set_ylabel("Frequency")

        elif chart_type == "Boxplot":
            excluded = [
                col for col in categorical_cols
                if df[col].nunique() > 10
            ]

            if excluded:
                st.caption(f"Excluded high-cardinality columns: {', '.join(excluded[:3])}...")
            if group_col != "None":
                groups = filtered_df[[group_col, y_col]].dropna()

                data = [
                    groups[groups[group_col] == cat][y_col]
                    for cat in groups[group_col].unique()
                ]

                bp = ax.boxplot(
                    data,
                    labels=groups[group_col].unique(),
                    patch_artist=True
                )

                palette = ["#2A6F97", "#52B788", "#F4A261", "#8E7DBE", "#E76F51"]

                for patch, color in zip(bp["boxes"], palette):
                    patch.set_facecolor(color)
                    patch.set_alpha(0.8)

                # style lines
                for median in bp["medians"]:
                    median.set_color("black")
                    median.set_linewidth(2)

                for whisker in bp["whiskers"]:
                    whisker.set_color("#555")

                for cap in bp["caps"]:
                    cap.set_color("#555")
                plt.xticks(rotation=45)

                ax.set_title(f"{y_col} by {group_col}")
            else:
                data = filtered_df[y_col].dropna()
                ax.boxplot(data, vert=True, patch_artist=True)

                ax.set_title(f"Boxplot of {y_col}")

            ax.set_ylabel(y_col)
            ax.grid(True, linestyle="--", alpha=0.3)

            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

        elif chart_type == "Scatter":
            data_cols = [x_col, y_col]
            if color_mode == "By category" and not categorical_cols:
                st.warning("No categorical columns available for coloring.")
            
            if color_mode == "By category" and color_col:
                data_cols.append(color_col)

            data = filtered_df[data_cols].dropna()

            plt.style.use("seaborn-v0_8")

            if color_mode == "By category" and color_col is not None:
                st.info("Tip: Too many categories may reduce readability. Start from filtering")
                palette = ["#2A6F97", "#52B788", "#F4A261", "#8E7DBE", "#E76F51"]

                for i, (cat, subset) in enumerate(data.groupby(color_col)):
                    x = subset[x_col] + np.random.normal(0, 0.2, size=len(subset))

                    ax.scatter(
                        x,
                        subset[y_col],
                        label=str(cat),
                        color=palette[i % len(palette)],   # 🎯 controlled colors
                        alpha=0.6,
                        s=30
                    )
                ax.legend(title=color_col, bbox_to_anchor=(1.05, 1), loc='upper left')


            else:
                ax.scatter(
                    data[x_col],
                    data[y_col],
                    color=color_value,
                    alpha=0.7,
                    s=25
                )
            ax.set_title(f"{x_col} vs {y_col}", fontsize=14)
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
            ax.grid(True, linestyle="--", alpha=0.3)
            


        elif chart_type == "Line":
            import matplotlib.dates as mdates

            if x_col is None or y_col is None:
                st.warning("Please select both time and value columns.")
                st.stop()

            data = filtered_df[[x_col, y_col]].dropna()

            if data.empty:
                st.warning("No data to plot.")
                st.stop()

            # =========================
            # SAFE DATETIME CONVERSION
            # =========================
            if data[x_col].dtype in ["int64", "float64"]:
                # try YYYYMMDD format first
                data[x_col] = pd.to_datetime(
                    data[x_col].astype(str),
                    format="%Y%m%d",
                    errors="coerce"
                )

                # fallback if failed
                if data[x_col].isna().mean() > 0.5:
                    data[x_col] = pd.to_datetime(data[x_col], errors="coerce")

            else:
                data[x_col] = pd.to_datetime(data[x_col], errors="coerce")

            data = data.dropna(subset=[x_col])

            if data.empty:
                st.error("Could not parse datetime column.")
                st.stop()

            # =========================
            # SORT (VERY IMPORTANT)
            # =========================
            data = data.sort_values(by=x_col)

            # =========================
            # TIME COMPLEXITY LOGIC
            # =========================
            month_periods = data[x_col].dt.to_period("M").nunique()

            # Decide behavior
            if month_periods <= 36:
                mode = "monthly"
            elif month_periods <= 60:
                mode = "monthly_sparse"
            else:
                mode = "yearly"

            # =========================
            # PREPARE DATA
            # =========================
            if mode == "yearly":
                data["time_group"] = data[x_col].dt.year
                data = data.groupby("time_group")[y_col].mean().reset_index()

            else:
                data["time_group"] = data[x_col].dt.to_period("M").dt.to_timestamp()
                data = data.groupby("time_group")[y_col].mean().reset_index()

            # smoothing (light, keeps shape)
            data[y_col] = data[y_col].rolling(window=3, min_periods=1).mean()

            # =========================
            # PLOT
            # =========================
            ax.plot(
                data["time_group"],
                data[y_col],
                color="#2A6F97",
                linewidth=2.5,
                alpha=0.9
            )

            # =========================
            # AXIS FORMATTING
            # =========================
            if mode in ["monthly", "monthly_sparse"]:

                # dynamic interval
                if month_periods <= 12:
                    interval = 1
                elif month_periods <= 24:
                    interval = 2
                elif month_periods <= 36:
                    interval = 3
                else:
                    interval = 6

                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=interval))
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

            else:
                ax.set_xticks(data["time_group"])
                ax.set_xticklabels(data["time_group"].astype(str))

            plt.xticks(rotation=30)

            # =========================
            # STYLE
            # =========================
            ax.set_title(f"{y_col} Trend Over Time", fontsize=14, fontweight="semibold")
            ax.set_xlabel("Time")
            ax.set_ylabel(y_col)

            ax.grid(True, linestyle="--", alpha=0.2)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

            plt.tight_layout()
        elif chart_type == "Bar":

            if filtered_df.empty:
                st.error("No data available.")
                st.stop()

            # ======================
            # COUNT (no y_col needed)
            # ======================
            if agg == "count":
                grouped = (
                    filtered_df[x_col]
                    .value_counts()
                    .head(top_n)
                )

            # ======================
            # OTHER AGGREGATIONS
            # ======================
            else:
                if y_col is None:
                    st.warning("Select a numeric column for aggregation.")
                    st.stop()

                grouped = (
                    filtered_df.groupby(x_col)[y_col]
                    .agg(agg)
                    .sort_values(ascending=False)
                    .head(top_n)
                )

            if grouped.empty:
                st.warning("No data to display.")
                st.stop()

            # ======================
            # PLOT
            # ======================
            palette = ["#2A6F97", "#52B788", "#E76F51", "#E9C46A", "#6D597A"]
            colors = [palette[i % len(palette)] for i in range(len(grouped))]

            ax.bar(
                grouped.index.astype(str),
                grouped.values,
                color=colors,
                alpha=0.85
            )

            # labels on top
            for i, v in enumerate(grouped.values):
                ax.text(i, v, f"{int(v)}", ha='center', va='bottom', fontsize=9)

            if y_col:
                ax.set_title(f"{agg.capitalize()} of {y_col} by {x_col}")
            else:
                ax.set_title(f"{agg.capitalize()} of {x_col}")
            ax.set_xlabel(x_col)
            ax.set_ylabel(agg)

            ax.grid(True, axis='y', linestyle="--", alpha=0.2)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

            plt.tight_layout()
        elif chart_type == "Heatmap":
            import numpy as np

            # Create 1–5 scales
            likelihood = np.arange(1, 6)
            severity = np.arange(1, 6)
            corr_df = filtered_df[selected_cols].copy()

            # remove ID-like columns
            corr_df = corr_df.loc[:, corr_df.nunique() > 1]

            corr = corr_df.corr()
            if (abs(corr.values[np.triu_indices_from(corr, 1)]) < 0.1).all():
                st.info("No strong correlations found. Variables appear independent.")

            fig, ax = plt.subplots(figsize=(6, 5))

            cax = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)

            # ticks
            ax.set_xticks(range(len(corr.columns)))
            ax.set_yticks(range(len(corr.columns)))

            ax.set_xticklabels(corr.columns, rotation=45, ha="right")
            ax.set_yticklabels(corr.columns)

            # values inside cells
            for i in range(len(corr)):
                for j in range(len(corr)):
                    ax.text(j, i, f"{corr.iloc[i, j]:.2f}".replace("-0.00", "0.00"),
                            ha="center", va="center", color="black")

            # color bar
            fig.colorbar(cax)

            # style
            ax.set_title("Correlation between Selected Features", fontsize=14)
            ax.grid(False)

            plt.tight_layout()

    except Exception as e:
        st.error(f"Error: {e}")
        st.stop()


    if x_col:
        ax.set_xlabel(x_col)
    if y_col:
        ax.set_ylabel(y_col)

    st.pyplot(fig)


# =========================
# TRANSFORMATION LOG (SIDEBAR)
# =========================
st.sidebar.markdown("## 🧾 Transformations")

logs = st.session_state.get("log", [])

if logs:
    recent_logs = logs[-5:]  # last 5 only

    for entry in reversed(recent_logs):
        st.sidebar.markdown(f"""
**{entry.get('operation', '-') }**

• {entry.get('action', '-')}  
• `{entry.get('columns', '-')}`
""")
    
    with st.sidebar.expander("View full log"):
        for entry in reversed(logs):
            st.markdown(f"""
**{entry.get('operation', '-') }**

- Column: `{entry.get('columns', '-')}`
- Method: `{entry.get('method', '-')}`
- Action: `{entry.get('action', '-')}`
- Details: `{entry.get('details', '-')}`
""")
else:
    st.sidebar.caption("No transformations yet")