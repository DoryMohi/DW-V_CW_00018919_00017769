import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime

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
numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
categorical_cols = [
    col for col in df.select_dtypes(include=["object", "category", "string"]).columns
    if 2 <= df[col].nunique() <= 10
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
    y_col = st.selectbox("Value", numeric_cols)

    color_col = st.selectbox(
        "Group by (optional)",
        ["None"] + categorical_cols
    )

    agg = st.selectbox("Aggregation", ["sum", "mean", "count", "median"])

    if color_col != "None":
        max_groups = df[color_col].nunique()
        top_n = st.slider("Top N categories", 2, max_groups, min(5, max_groups))
    else:
        top_n = st.slider("Top N categories", 2, 20, 10)
    
    st.caption("Top N categories will be updated based on the filtered data.")

elif chart_type == "Heatmap":
    selected_cols = st.multiselect(
    "Select numeric columns",
    numeric_cols,
    default=numeric_cols[:3]
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

            counts, bins, patches = ax.hist(data, bins=bins)

            # 🔥 gradient colors
            for i, patch in enumerate(patches):
                patch.set_alpha(0.8)
                patch.set_edgecolor("white")

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

                ax.boxplot(data, labels=groups[group_col].unique(), patch_artist=True)
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
                for cat, subset in data.groupby(color_col):
                    x = subset[x_col] + np.random.normal(0, 0.2, size=len(subset))
                    ax.scatter(
                        x,
                        subset[y_col],
                        label=str(cat),
                        alpha=0.5,
                        s=25
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

            data = filtered_df[[x_col, y_col]].dropna()
            data = data.sort_values(by=x_col)

            if group_col != "None":
                for cat, subset in filtered_df.groupby(group_col):
                    subset = subset[[x_col, y_col]].dropna()
                    subset = subset.sort_values(by=x_col)

                    subset = subset.groupby(x_col)[y_col].mean().reset_index()

                    # 🔥 smoothing
                    subset = subset.groupby(x_col)[y_col].mean().reset_index()
                    subset[y_col] = subset[y_col].rolling(window=60, min_periods=10).mean()

                    ax.plot(
                        subset[x_col],
                        subset[y_col],
                        label=str(cat),
                        linewidth=2
                    )

                ax.legend(
                    title=group_col,
                    bbox_to_anchor=(1.05, 1),
                    loc='upper left'
                )

            else:
                data = data.groupby(x_col)[y_col].mean().reset_index()

                # 🔥 smoothing
                data[y_col] = data[y_col].rolling(window=60, min_periods=1).mean()

                ax.plot(
                    data[x_col],
                    data[y_col],
                    color="blue",
                    linewidth=2
                )

            ax.set_title(f"Smoothed {y_col} over {x_col}")
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)


            # ✅ Clean date axis
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            plt.xticks(rotation=30)

            # ✅ Clean Y ticks
            ax.yaxis.set_major_locator(plt.MaxNLocator(6))

            # ✅ Light grid
            ax.grid(True, linestyle="--", alpha=0.2)

            # ✅ Remove ugly borders
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

            # Optional: slightly stronger axes
            ax.spines['left'].set_linewidth(1.2)
            ax.spines['bottom'].set_linewidth(1.2)

            # prevent legend cut-off
            plt.tight_layout()

        elif chart_type == "Bar":
            import numpy as np

            fig, ax = plt.subplots(figsize=(8, 5))

            # =========================
            # GROUPED BAR
            # =========================
            if color_col != "None":

                # calculate on full dataset
                base_grouped = df.groupby([x_col, color_col])[y_col].mean().unstack()
                top_groups = base_grouped.mean().sort_values(ascending=False).head(top_n).index

                # apply to filtered
                grouped = filtered_df.groupby([x_col, color_col])[y_col].mean().unstack()
                grouped = grouped[top_groups]

                if grouped.shape[1] > 5:
                    st.warning("Too many categories for grouped bar chart. Consider filtering.")

                x = np.arange(len(grouped.index))
                width = 0.8 / len(grouped.columns)

                for i, col in enumerate(grouped.columns):
                    ax.bar(
                        x + i * width,
                        grouped[col],
                        width=width,
                        label=str(col),
                        alpha=0.9
                    )

                ax.set_xticks(x + width * (len(grouped.columns) - 1) / 2)
                ax.set_xticklabels(grouped.index.astype(str), rotation=30)

                ax.legend(
                    title=color_col,
                    bbox_to_anchor=(1.05, 1),
                    loc='upper left'
                )

            # =========================
            # SIMPLE BAR
            # =========================
            else:
                grouped = filtered_df.groupby(x_col)[y_col].mean() \
                    .sort_values(ascending=False).head(top_n)

                bars = ax.bar(grouped.index.astype(str), grouped.values)

                for bar in bars:
                    bar.set_alpha(0.85)

            # =========================
            # STYLE
            # =========================
            ax.set_title(f"{y_col} by {x_col}", fontsize=14)
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)

            ax.grid(True, axis='y', linestyle="--", alpha=0.2)

            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

            plt.tight_layout()

        elif chart_type == "Heatmap":
            import numpy as np

            # Create 1–5 scales
            likelihood = np.arange(1, 6)
            severity = np.arange(1, 6)
            corr = filtered_df[selected_cols].corr()

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