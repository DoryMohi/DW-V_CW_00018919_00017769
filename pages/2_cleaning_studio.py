import streamlit as st
import pandas as pd
from scipy import stats
import numpy as np


st.title("Page B — Cleaning & Preparation Studio")

if "df" not in st.session_state:
    st.warning("Upload data first in Page A.")
    st.stop()

df = st.session_state["df"]

st.subheader("Dataset Control")

if "original_df" in st.session_state:
    if st.button("Reset to Original Data"):
        st.session_state["df"] = st.session_state["original_df"].copy()
        st.success("Dataset restored!")
        st.rerun()
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

missing_col = st.selectbox(
    "Select column",
    df.columns,
    key="missing_col"
)

is_numeric = pd.api.types.is_numeric_dtype(df[missing_col])

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

missing_action = st.selectbox(
    "Choose action",
    actions,
    key="missing_action"
)
value = None
if missing_action == "Fill with constant":
    value = st.text_input(f"Enter value for {missing_col}")

# ------------------ BEFORE INFO ------------------

before_rows = len(df)

# ------------------ APPLY BUTTON ------------------

if st.button("Apply Missing Value Operation"):

    df_copy = df.copy()

    try:
        if missing_action in ["Fill with mean", "Fill with median"] and not is_numeric:
            st.error("Only numeric columns allowed.")
            st.stop() 
        if missing_action == "Drop rows":
            df_copy = df_copy.dropna(subset=[missing_col])

        elif missing_action == "Fill with mean":
            df_copy[missing_col] = df_copy[missing_col].fillna(df_copy[missing_col].mean())

        elif missing_action == "Fill with median":
            df_copy[missing_col] = df_copy[missing_col].fillna(df_copy[missing_col].median())

        elif missing_action == "Fill with mode":
            df_copy[missing_col] = df_copy[missing_col].fillna(df_copy[missing_col].mode()[0])

        elif missing_action == "Fill with constant":
            if value:
                df_copy[missing_col] = df_copy[missing_col].fillna(value)
            else:
                st.warning("Enter a value first.")
                st.stop()

        elif missing_action == "Forward fill":
            df_copy[missing_col] = df_copy[missing_col].fillna(method="ffill")

        elif missing_action == "Backward fill":
            df_copy[missing_col] = df_copy[missing_col].fillna(method="bfill")

        # SAVE
        if "original_df" not in st.session_state:
             st.session_state["original_df"] = df.copy()

        st.session_state["df"] = df_copy

        st.success("Operation applied!")
        st.write("Missing before:", df[missing_col].isnull().sum())
        st.write("Missing after:", df_copy[missing_col].isnull().sum())
        st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")
    

# ------------------ DUPLICATES ------------------

st.subheader("Handle Duplicates")

dup_type = st.radio(
    "Select duplicate type",
    ["Full row duplicates", "Subset duplicates"]
)
subset_cols = None

if dup_type == "Subset duplicates":
    subset_cols = st.multiselect("Select columns", df.columns)

if dup_type == "Full row duplicates":
    duplicates = df[df.duplicated()]
else:
    if subset_cols:
        duplicates = df[df.duplicated(subset=subset_cols)]
    else:
        duplicates = pd.DataFrame() 

st.write("Duplicate rows found:", len(duplicates))
if not duplicates.empty:
    st.dataframe(duplicates)

dup_action = st.selectbox(
    "Action",
    ["Do nothing", "Remove duplicates (keep first)", "Remove duplicates (keep last)"],
    key="dup_action"
)
if st.button("Apply Duplicate Operation"):

    df_copy = df.copy()   # ← MUST be first

    before_rows = len(df_copy)

    if dup_action == "Remove duplicates (keep first)":
        if dup_type == "Full row duplicates":
            df_copy = df_copy.drop_duplicates(keep="first")
        else:
            df_copy = df_copy.drop_duplicates(subset=subset_cols, keep="first")

    elif dup_action == "Remove duplicates (keep last)":
        if dup_type == "Full row duplicates":
            df_copy = df_copy.drop_duplicates(keep="last")
        else:
            df_copy = df_copy.drop_duplicates(subset=subset_cols, keep="last")


    after_rows = len(df_copy)

    st.session_state["df"] = df_copy


    if dup_action == "Do nothing":
        st.info("No changes applied.")

    elif len(duplicates) == 0:
        st.info("No duplicates found.")

    else:
        st.success("Duplicates removed!")

        st.write("Before rows:", before_rows)
        st.write("After rows:", after_rows)
    
    st.rerun()
if dup_type == "Subset duplicates" and not subset_cols:
    st.warning("Select at least one column.")
    st.stop()

# ------------------ Data Types & Parsing ------------------
st.subheader("Data Types & Parsing")
type_col = st.selectbox("Select column to convert", df.columns, key="type_col")

sample_values = df[type_col].dropna().astype(str).head(10)

def looks_like_datetime(values):
    try:
        pd.to_datetime(values, errors="raise")
        return True
    except:
        return False

def looks_like_numeric(values):
    try:
        pd.to_numeric(values, errors="raise")
        return True
    except:
        return False

# smarter options
if looks_like_numeric(sample_values):
    options = ["Numeric", "Categorical"]

elif looks_like_datetime(sample_values):
    options = ["Datetime", "Categorical"]

else:
    options = ["Categorical"]

target_type = st.selectbox(
    "Convert to",
    options,
    key="target_type"
)

date_format = None
if target_type == "Datetime":
    date_format = st.text_input("Enter datetime format (optional)")

st.write("Current type:", st.session_state["df"][type_col].dtype)
if st.button("Apply Type Conversion"):
    df_copy = df.copy()
    before_type = df[type_col].dtype

    st.write("Before:", before_type)

    try:
        if target_type == "Numeric" and not looks_like_numeric(sample_values):
            st.error("This column cannot be safely converted to numeric.")
            st.stop()

        if target_type == "Datetime" and not looks_like_datetime(sample_values):
            st.error("This column cannot be safely converted to datetime.")
            st.stop()

        if target_type == "Numeric":
            df_copy[type_col] = (
                df_copy[type_col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("$", "", regex=False)
            )
            df_copy[type_col] = pd.to_numeric(df_copy[type_col], errors="coerce")

        elif target_type == "Categorical":
            df_copy[type_col] = df_copy[type_col].astype("category")

        elif target_type == "Datetime":
            if date_format:
                df_copy[type_col] = pd.to_datetime(
                    df_copy[type_col], format=date_format, errors="coerce"
                )
            else:
                df_copy[type_col] = pd.to_datetime(
                    df_copy[type_col], errors="coerce"
                )

        after_type = df_copy[type_col].dtype
        st.write("After:", after_type)

        st.session_state["df"] = df_copy
        st.success("Column converted successfully!")
        st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")
# ------------------ Categorical Data Tools ------------------
st.subheader("Categorical Data Tools")

cat_cols = df.select_dtypes(include=["object", "string", "category"]).columns

if len(cat_cols) == 0:
    st.info("No categorical columns available.")
    st.stop()

cat_col = st.selectbox("Select categorical column", cat_cols, key="cat_col")
st.markdown("### Value Standardization")

std_action = st.selectbox(
    "Choose standardization",
    ["Trim whitespace", "Lowercase", "Uppercase", "Title case"],
    key="std_action"
)
if st.button("Apply Standardization"):
    df_copy = df.copy()

    if std_action == "Trim whitespace":
        df_copy[cat_col] = df_copy[cat_col].astype(str).str.strip()

    elif std_action == "Lowercase":
        df_copy[cat_col] = df_copy[cat_col].astype(str).str.lower()

    elif std_action == "Uppercase":
        df_copy[cat_col] = df_copy[cat_col].astype(str).str.upper()

    elif std_action == "Title case":
        df_copy[cat_col] = df_copy[cat_col].astype(str).str.title()

    st.session_state["df"] = df_copy

    st.success("Standardization applied!")
    st.rerun()

# ------------------  Mapping / Replacement ------------------

st.markdown("### Mapping / Replacement")

unique_vals = df[cat_col].dropna().unique()
st.write("Unique values:", unique_vals[:20])

old_val = st.text_input("Value to replace")
new_val = st.text_input("Replace with")

if st.button("Apply Mapping"):
    df_copy = df.copy()

    df_copy[cat_col] = df_copy[cat_col].replace(old_val, new_val)

    st.session_state["df"] = df_copy

    st.success("Mapping applied!")
    st.rerun()

# ------------------ Rare Category Grouping ------------------

st.markdown("### Rare Category Grouping")

cat_cols = df.select_dtypes(include=["object", "string", "category"]).columns

group_col = st.selectbox(
    "Select column for grouping",
    cat_cols,
    key="group_col_rare"
)

threshold = st.number_input("Minimum frequency", min_value=1, value=2)

# 🔹 ALWAYS compute preview (reactive)
df_preview = df.copy()

counts = df_preview[group_col].value_counts()
rare = counts[counts < threshold].index

df_preview[group_col] = df_preview[group_col].apply(
    lambda x: "Other" if pd.notnull(x) and x in rare else x
)

# 🔹 DISPLAY ONE TABLE ONLY
st.write("Category frequency:")
st.dataframe(df_preview[group_col].value_counts())


  # ------------------ One-Hot Encoding ------------------

st.subheader("One-Hot Encoding")

valid_ohe_cols = [col for col in cat_cols if df[col].nunique() < 20]
ohe_col = st.selectbox("Select column for encoding", valid_ohe_cols, key="ohe_col")

if df[ohe_col].nunique() > 50:
    st.warning("⚠️ This column has many unique values. One-hot encoding may create too many columns.")

if st.button("Apply One-Hot Encoding"):
    df_copy = df.copy()

    df_copy = pd.get_dummies(df_copy, columns=[ohe_col], drop_first=True)
    new_cols = [c for c in df_copy.columns if ohe_col in c]
    df_copy[new_cols] = df_copy[new_cols].astype(int)

    st.session_state["df"] = df_copy
    st.session_state["ohe_done"] = True
    st.session_state["ohe_col_done"] = ohe_col

    st.rerun()

if st.session_state.get("ohe_done"):
    st.success(f"One-hot encoding applied on '{st.session_state['ohe_col_done']}'")

    new_cols = [c for c in st.session_state["df"].columns if st.session_state["ohe_col_done"] in c]
    st.write(f"Created {len(new_cols)} new columns")
    st.session_state["ohe_done"] = False
    st.write(new_cols[:10])

# ------------------ Outlier Detection & Handling ------------------
st.subheader("Outlier Detection & Handling")

all_num_cols = df.select_dtypes(include=["int64", "float64"]).columns

num_cols = [
    col for col in all_num_cols
    if df[col].nunique() > 5
]

if len(num_cols) == 0:
    st.info("No suitable numeric columns available.")
    st.stop()

out_col = st.selectbox(
    "Select numeric column",
    num_cols,
    key="outlier_col"
)
outlier_method = st.selectbox(
    "Detection method",
    ["IQR", "Z-score"],
    key="outlier_method"
)

outlier_action = st.selectbox(
    "Choose action",
    ["Do nothing", "Cap (Winsorize)", "Remove outliers"],
    key="outlier_action"
)

if len(num_cols) < len(all_num_cols):
    st.caption("Binary or low-variance columns were excluded.")
if outlier_method == "IQR":
    Q1 = df[out_col].quantile(0.25)
    Q3 = df[out_col].quantile(0.75)
    IQR = Q3 - Q1

    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR

    outliers = df[(df[out_col] < lower) | (df[out_col] > upper)]

elif outlier_method == "Z-score":
    std = df[out_col].std()

    if std == 0:
        st.warning("Standard deviation is 0. Cannot compute Z-score.")
        outliers = df.iloc[0:0]
    else:
        z_scores = (df[out_col] - df[out_col].mean()) / std
        outliers = df[np.abs(z_scores) > 3]

    lower = None
    upper = None

# ------------------ DISPLAY ------------------

st.write("Total rows:", len(df))
st.write(f"Outliers found ({outlier_method}):", len(outliers))

if outlier_method == "IQR":
    st.write("Lower bound:", lower)
    st.write("Upper bound:", upper)

st.dataframe(outliers.head(10))

# ------------------ ADD TEST OUTLIERS ------------------

if st.button("Add Test Outliers"):
    df_copy = df.copy()

    df_copy.loc[0, out_col] = df_copy[out_col].max() * 10
    df_copy.loc[1, out_col] = df_copy[out_col].min() * 10
    df_copy.loc[2, out_col] = df_copy[out_col].min() * 10
    df_copy.loc[3, out_col] = df_copy[out_col].min() * 10

    st.session_state["df"] = df_copy
    st.success("Test outliers added!")
    st.rerun()

# ------------------ APPLY OPERATION ------------------

if st.button("Apply Outlier Operation"):

    df_copy = df.copy()

    if outlier_action == "Do nothing":
        st.info("No changes applied.")

    else:
        before_rows = len(df)

        if outlier_action == "Remove outliers":

            if outlier_method == "IQR":
                df_copy = df_copy[(df_copy[out_col] >= lower) & (df_copy[out_col] <= upper)]

            elif outlier_method == "Z-score":
                std = df_copy[out_col].std()
                if std != 0:
                    z_scores = (df_copy[out_col] - df_copy[out_col].mean()) / std
                    df_copy = df_copy[np.abs(z_scores) <= 3]

            removed = before_rows - len(df_copy)

        elif outlier_action == "Cap (Winsorize)":

            before_values = df_copy[out_col].copy()

            if outlier_method == "IQR":
                df_copy[out_col] = df_copy[out_col].clip(lower, upper)

            elif outlier_method == "Z-score":
                st.warning("Capping not supported for Z-score")

            changed = (before_values != df_copy[out_col]).sum()

        # SAVE
        st.session_state["df"] = df_copy
        st.success("Outlier handling applied!")

        st.write("Rows before:", before_rows)
        st.write("Rows after:", len(df_copy))

        if outlier_action == "Remove outliers":
            st.write("Rows removed:", removed)

        elif outlier_action == "Cap (Winsorize)":
            st.write("Values capped:", changed)

        st.rerun()

# ------------------ Normalization / Scaling ------------------
st.subheader("Normalization / Scaling")

num_cols = df.select_dtypes(include=["int64", "float64"]).columns

if len(num_cols) == 0:
    st.info("No numeric columns available.")
    st.stop()

scale_cols = st.multiselect("Select columns to scale", num_cols)

scaling_method = st.selectbox(
    "Scaling method",
    ["Min-Max", "Z-score"],
    key="scaling_method"
)
# BEFORE STATS
if scale_cols:
    st.markdown("### Before Scaling")
    st.dataframe(df[scale_cols].describe())

# APPLY
if st.button("Apply Scaling"):

    df_copy = df.copy()

    for col in scale_cols:
        if scaling_method == "Min-Max":
            min_val = df_copy[col].min()
            max_val = df_copy[col].max()
            if max_val != min_val:
                df_copy[col] = (df_copy[col] - min_val) / (max_val - min_val)

        elif scaling_method == "Z-score":
            mean = df_copy[col].mean()
            std = df_copy[col].std()
            if std != 0:
                df_copy[col] = (df_copy[col] - mean) / std

    st.session_state["df"] = df_copy
    st.success("Scaling applied!")

    st.markdown("### After Scaling")
    st.dataframe(df_copy[scale_cols].describe().round(3))
    st.rerun()


# ------------------ Rename Columns ------------------

st.subheader("Rename Columns")

rename_col = st.selectbox(
    "Select column to rename",
    df.columns,
    key="rename_col"
)
new_name = st.text_input("Enter new column name")

if st.button("Rename Column"):
    if new_name.strip() == "":
        st.warning("Enter a valid name.")
    else:
        df_copy = df.copy()
        df_copy = df_copy.rename(columns={rename_col: new_name})
        st.session_state["df"] = df_copy
        st.success(f"{rename_col} renamed to {new_name}")

        st.rerun()

st.subheader("Drop Columns")

drop_cols = st.multiselect("Select columns to drop", df.columns)

if st.button("Drop Selected Columns"):
    if not drop_cols:
        st.warning("Select at least one column.")
    else:
        df_copy = df.copy()
        df_copy = df_copy.drop(columns=drop_cols)
        st.session_state["df"] = df_copy
        st.success(f"Dropped columns: {drop_cols}")
        st.rerun()

    


st.subheader("Create New Column")

new_col_name = st.text_input("New column name")

formula_type = st.selectbox(
    "Select formula",
    ["Addition", "Subtraction", "Division", "Log", "Mean Difference"],
    key="formula_type"
)

col1 = st.selectbox("Column 1", df.columns, key="f_col1")
col2 = st.selectbox("Column 2", df.columns, key="f_col2")

if st.button("Create Column"):
    df_copy = df.copy()

    try:
        if formula_type == "Addition":
            df_copy[new_col_name] = df_copy[col1] + df_copy[col2]

        elif formula_type == "Subtraction":
            df_copy[new_col_name] = df_copy[col1] - df_copy[col2]

        elif formula_type == "Division":
            df_copy[new_col_name] = df_copy[col1] / df_copy[col2]

        elif formula_type == "Log":
            df_copy[new_col_name] = np.log(df_copy[col1].replace(0, np.nan))

        elif formula_type == "Mean Difference":
            df_copy[new_col_name] = df_copy[col1] - df_copy[col1].mean()

        st.session_state["df"] = df_copy
        st.success(f"Column '{new_col_name}' created!")
        st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")   


st.subheader("Binning (Discretization)")

bin_col = st.selectbox(
    "Select numeric column",
    num_cols,
    key="bin_col"
)
bins = st.number_input("Number of bins", min_value=2, value=4)

bin_method = st.selectbox(
    "Binning method",
    ["Equal Width", "Quantile"],
    key="bin_method"
)
new_bin_col = st.text_input("New binned column name")


if st.button("Apply Binning"):
    if not new_bin_col:
        st.warning("Enter a name for new column.")
    else:
        df_copy = df.copy()
    try:
        if bin_method == "Equal Width":
            df_copy[new_bin_col] = pd.cut(df_copy[bin_col], bins=bins)
            df_copy[new_bin_col] = df_copy[new_bin_col].astype(str)

        elif bin_method == "Quantile":
            df_copy[new_bin_col] = pd.qcut(df_copy[bin_col], q=bins, duplicates="drop")
            df_copy[new_bin_col] = df_copy[new_bin_col].astype(str)

        st.session_state["df"] = df_copy

        st.success(f"Binning applied on {bin_col}")

        st.write("Value counts:")
        st.write(df_copy[new_bin_col].value_counts())
        st.rerun()


    except Exception as e:
        st.error(f"Error: {e}")
  # ------------------ Download Cleaned Dataset ------------------

st.subheader("Download Cleaned Dataset")

csv = st.session_state["df"].to_csv(index=False)

st.download_button(
    label="Download CSV",
    data=csv,
    file_name="cleaned_dataset.csv",
    mime="text/csv"
)