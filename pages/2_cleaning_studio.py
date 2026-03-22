import streamlit as st
import pandas as pd
from scipy import stats
import numpy as np

# ------------------ STYLE ------------------
st.markdown("""
<style>
.section { margin-top: 30px; }

.card {
    background: #F9FAFB;
    padding: 18px;
    border-radius: 10px;
    border: 1px solid #E5E7EB;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

st.title("Page B — Cleaning & Preparation Studio")

df = st.session_state.get("df")

if df is None:
    st.warning("⚠️ Upload a dataset first from Page A.")
    st.stop()
if "log" not in st.session_state:
    st.session_state["log"] = []

df = df.copy().convert_dtypes()

# =====================================================
# ⚙️ DATASET CONTROL
# =====================================================
st.markdown("## Dataset Control")

if "original_df" in st.session_state:
        if st.button("🔄 Reset to Original Data"):
            st.session_state["df"] = st.session_state["original_df"].copy()

            if "log" in st.session_state:
                st.session_state["log"].append("Reset → Restored original dataset")
                
            st.session_state["log"].append(
                f"Reset → Restored original dataset ({len(df)} rows)"
)
            st.success("Dataset restored.")
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# 🧹 MISSING VALUES
# =====================================================
st.markdown("## Missing Values")

missing = df.isnull().sum()
missing_df = pd.DataFrame({
    "Missing Count": missing,
    "Missing %": ((missing / len(df)) * 100).round(2)
}).sort_values(by="Missing Count", ascending=False)

st.markdown("### 📊 Summary")
st.dataframe(missing_df, width="stretch")

# ------------------ DROP BY THRESHOLD ------------------
st.markdown("### 🚫 Drop Columns by Missing %")

threshold = st.slider(
    "Missing value threshold (%)",
    min_value=0.0,
    max_value=15.0,
    value=0.1,
    step=0.01,
    help="Columns with missing percentage above this value will be removed"
)

percent = (df.isnull().sum() / len(df)) * 100
cols_to_drop = percent[percent > threshold].index.tolist()

# PREVIEW
if cols_to_drop:
    st.markdown(f"### Columns to drop (>{threshold}%)")
    for col in cols_to_drop:
        st.markdown(f"- {col}")
    st.markdown(f"**{len(cols_to_drop)} columns will be removed**")
else:
    st.info("No columns exceed the selected threshold.")

# APPLY
if st.button("🗑️ Apply Column Drop", type="primary"):

    if not cols_to_drop:
        st.info("No columns exceed the selected threshold.")
    else:
        df_copy = df.copy()
        before_cols = len(df.columns)

        df_copy = df_copy.drop(columns=cols_to_drop)

        after_cols = len(df_copy.columns)

        st.session_state["df"] = df_copy

        if "log" in st.session_state:
            st.session_state["log"].append(
                f"Drop columns > {threshold}% → {cols_to_drop}"
            )

        st.success("✔ Columns dropped!")
        st.markdown(f"**Columns before:** {before_cols}")
        st.markdown(f"**Columns after:** {after_cols}")

        st.rerun()

st.markdown("---")


# ------------------ HANDLE MISSING ------------------
st.markdown("### ⚙️ Handle Missing Values")

col1, col2 = st.columns(2)

with col1:
    missing_col = st.selectbox("Column", df.columns)

is_numeric = pd.api.types.is_numeric_dtype(df[missing_col])

if is_numeric:
    actions = [
        "Drop rows",
        "Fill with mean",
        "Fill with median",
        "Fill with most frequent",
        "Fill with constant",
        "Forward fill",
        "Backward fill"
    ]
else:
    actions = [
        "Drop rows",
        "Fill with most frequent",
        "Fill with constant",
        "Forward fill",
        "Backward fill"
    ]

with col2:
    missing_action = st.selectbox("Action", actions)

value = None
if missing_action == "Fill with constant":
    value = st.text_input("Enter value")

# APPLY
if st.button("Apply Changes", type="secondary"):

    before_missing = df[missing_col].isnull().sum()
    before_rows = len(df)

    no_missing = before_missing == 0

    if no_missing:
        st.info(f"No missing values in '{missing_col}'. Nothing to clean.")

    else:
        try:
            df_copy = df.copy()

            if missing_action == "Drop rows":
                df_copy = df_copy.dropna(subset=[missing_col])

            elif missing_action == "Fill with mean":
                df_copy[missing_col] = df_copy[missing_col].fillna(df_copy[missing_col].mean())

            elif missing_action == "Fill with median":
                df_copy[missing_col] = df_copy[missing_col].fillna(df_copy[missing_col].median())

            elif missing_action == "Fill with most frequent":
                df_copy[missing_col] = df_copy[missing_col].fillna(df_copy[missing_col].mode()[0])

            elif missing_action == "Fill with constant":
                if not value:
                    st.warning("Enter a value first.")
                    st.stop()
                df_copy[missing_col] = df_copy[missing_col].fillna(value)

            elif missing_action == "Forward fill":
                df_copy[missing_col] = df_copy[missing_col].ffill()

            elif missing_action == "Backward fill":
                df_copy[missing_col] = df_copy[missing_col].bfill()

            # AFTER PREVIEW
            after_missing = df_copy[missing_col].isnull().sum()
            after_rows = len(df_copy)

            st.session_state["df"] = df_copy
            st.session_state["preview"] = {
                        "before_missing": before_missing,
                        "after_missing": after_missing,
                        "before_rows": before_rows,
                        "after_rows": after_rows,
                        "column": missing_col
                    }
            if "log" in st.session_state:
                st.session_state["log"].append(
                    f"Missing → {missing_action} on '{missing_col}'"
                )

            st.success("✔ Operation applied")

        except Exception as e:
            st.error(f"Error: {e}")

    if "preview" in st.session_state and not no_missing:
        p = st.session_state["preview"]
        st.markdown("### 📊 Before vs After")
        st.markdown(f"**Column affected:** {p['column']}")

        col_b, col_a = st.columns(2)

        with col_b:
            st.markdown("**Before**")
            st.write(f"Missing: {p['before_missing']}")
            st.write(f"Rows: {p['before_rows']}")

        with col_a:
            st.markdown("**After**")
            st.write(f"Missing: {p['after_missing']}")
            st.write(f"Rows: {p['after_rows']}")

st.markdown("---")

# =====================================================
# 🔁 DUPLICATES
# =====================================================
st.markdown("## 🔁 Duplicates")

dup_type = st.radio(
    "Duplicate type",
    ["Full row duplicates", "Subset duplicates"],
    index=0
)

subset_cols = []

# ---- SUBSET SELECTION ----
if dup_type == "Subset duplicates":
    subset_cols = st.multiselect("Select columns", df.columns)

    if not subset_cols:
        st.warning("Select at least one column to detect duplicates.")
        duplicates = pd.DataFrame()
    else:
        duplicates = df[df.duplicated(subset=subset_cols)]
else:
    duplicates = df[df.duplicated()]

# ---- SHOW DUPLICATES ----
st.write(f"Duplicates found: {len(duplicates)}")

if not duplicates.empty:
    st.dataframe(duplicates, width="stretch")
else:
    if dup_type == "Subset duplicates" and not subset_cols:
        pass  # don't confuse user
    else:
        st.info("No duplicates found.")

# ---- ACTION ----
if duplicates.empty:
    dup_action = st.selectbox(
        "Action",
        ["Do nothing"],
        disabled=True
    )
else:
    dup_action = st.selectbox(
        "Action",
        ["Do nothing", "Remove duplicates (keep first)", "Remove duplicates (keep last)"]
    )

# ---- APPLY ----
    disabled = duplicates.empty or dup_action == "Do nothing"

    if st.button("Apply Duplicate Operation", disabled=disabled):
        df_copy = df.copy()
        before_rows = len(df_copy)


        if dup_action == "Remove duplicates (keep first)":
            df_copy = df_copy.drop_duplicates(
                subset=subset_cols if subset_cols else None,
                keep="first"
            )

        elif dup_action == "Remove duplicates (keep last)":
            df_copy = df_copy.drop_duplicates(
                subset=subset_cols if subset_cols else None,
                keep="last"
            )


        after_rows = len(df_copy)
        removed = before_rows - after_rows

        st.session_state["df"] = df_copy

        # Save preview ONLY if something meaningful happened
        st.session_state["dup_preview"] = {
            "type": dup_type,
            "before_rows": before_rows,
            "after_rows": after_rows,
            "removed": removed
        }

        st.session_state["dup_applied"] = True

        if "log" in st.session_state and dup_action != "Do nothing":
            st.session_state["log"].append(f"Duplicates → {dup_action}")

        if dup_action == "Do nothing":
            st.info("No changes applied.")
        elif removed == 0:
            st.info("No duplicates to remove.")
        else:
            st.success("✔ Duplicates removed")
        st.session_state["log"].append(
        f"Duplicates → {dup_action} (subset={subset_cols})"
        )

        st.rerun()

# ---- RESULT ----
if (
    "dup_preview" in st.session_state
    and st.session_state.get("dup_applied")
):
    p = st.session_state["dup_preview"]

    # Only show result if something actually changed
    if p["removed"] > 0:
        st.markdown("### 🔍 Result")
        st.caption("Last operation result")
        st.markdown(f"**Type:** {p['type']}")

        col_b, col_a = st.columns(2)

        with col_b:
            st.markdown("**Before**")
            st.write(f"Rows: {p['before_rows']}")

        with col_a:
            st.markdown("**After**")
            st.write(f"Rows: {p['after_rows']}")

        percent = (p['removed'] / p['before_rows']) * 100
        st.write(f"Removed: {p['removed']} rows ({percent:.2f}%)")
st.markdown("---")
# ------------------ Data Types & Parsing ------------------
st.markdown("## 🧩 Data Types & Parsing")

df = st.session_state["df"]

# -------- SELECT COLUMN --------
type_col = st.selectbox("Select column to convert", df.columns, key="type_col")

sample_values = df[type_col].dropna().astype(str).head(20)
current_type = df[type_col].dtype


# -------- DETECTION FUNCTIONS --------
def looks_like_datetime(values):
    converted = pd.to_datetime(values, errors="coerce", format="mixed")
    return converted.notna().mean() > 0.7


def looks_like_numeric(values):
    try:
        pd.to_numeric(values, errors="raise")
        return True
    except:
        return False


# -------- SMART OPTIONS --------
if looks_like_numeric(sample_values):
    options = ["Numeric", "Categorical"]

elif looks_like_datetime(sample_values):
    options = ["Datetime", "Categorical"]

else:
    options = ["Categorical"]


target_type = st.selectbox("Convert to", options, key="target_type")


# -------- EXTRA OPTIONS --------
date_format = None
parse_mode = None
clean_numeric = False

if target_type == "Datetime":
    parse_mode = st.radio(
        "Parsing mode",
        ["Auto parse", "Specify format"]
    )

    if parse_mode == "Specify format":
        date_format = st.text_input("Enter datetime format (e.g. %Y-%m-%d)")


if target_type == "Numeric":
    clean_numeric = st.checkbox("Clean dirty values (remove $, commas)")


# -------- CURRENT TYPE --------
st.markdown(f"**Current type:** `{current_type}`")


# -------- APPLY BUTTON LOGIC --------
disabled = False

if target_type == "Datetime" and str(current_type).startswith("datetime"):
    disabled = True

if target_type == "Numeric" and "int" in str(current_type) or "float" in str(current_type):
    disabled = True


# -------- APPLY --------
if st.button("Apply Type Conversion", disabled=disabled):

    df_copy = df.copy()
    before_type = df[type_col].dtype
    before_na = df[type_col].isna().sum()

    try:
        # -------- NUMERIC --------
        if target_type == "Numeric":

            if clean_numeric:
                df_copy[type_col] = (
                    df_copy[type_col]
                    .astype(str)
                    .str.replace(",", "", regex=False)
                    .str.replace("$", "", regex=False)
                )

            df_copy[type_col] = pd.to_numeric(df_copy[type_col], errors="coerce")

        # -------- CATEGORICAL --------
        elif target_type == "Categorical":
            df_copy[type_col] = df_copy[type_col].astype("category")

        # -------- DATETIME --------
        elif target_type == "Datetime":

            if parse_mode == "Specify format" and date_format:
                df_copy[type_col] = pd.to_datetime(
                    df_copy[type_col],
                    format=date_format,
                    errors="coerce"
                )
            else:
                df_copy[type_col] = pd.to_datetime(
                    df_copy[type_col],
                    errors="coerce",
                    format="mixed"
                )

        after_type = df_copy[type_col].dtype
        after_na = df_copy[type_col].isna().sum()

        # -------- SAVE --------
        st.session_state["df"] = df_copy

        # -------- LOG --------
        if "log" in st.session_state:
            st.session_state["log"].append(
                f"Type → {type_col} → {target_type}"
            )

        # -------- SUCCESS --------
        st.success("✔ Type conversion applied")

        # -------- RESULT --------
        st.markdown("### 🔍 Result")
        st.caption("Last operation result")

        col_b, col_a = st.columns(2)

        with col_b:
            st.markdown("**Before**")
            st.write(f"Type: {before_type}")
            st.write(f"Missing: {before_na}")

        with col_a:
            st.markdown("**After**")
            st.write(f"Type: {after_type}")
            st.write(f"Missing: {after_na}")

        # -------- WARNINGS --------
        failed = after_na - before_na
        if failed > 0:
            st.warning(f"{failed} values could not be parsed and became NaN/NaT")

        st.session_state["log"].append(
            f"Type conversion → {type_col}: {before_type} → {after_type}"
        )
        st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")
st.markdown("---")

# ------------------ Categorical Data Tools ------------------
st.markdown("## 🏷️ Categorical Data Tools")

df = st.session_state["df"]
cat_cols = df.select_dtypes(include=["object", "category"]).columns

if len(cat_cols) == 0:
    st.info("No categorical columns available.")
    st.stop()

# =========================================================
# 1️⃣ VALUE STANDARDIZATION
# =========================================================
st.markdown("### 🔧 Value Standardization")

std_col = st.selectbox("Select column", cat_cols, key="std_col")

std_option = st.selectbox(
    "Choose standardization",
    ["Trim whitespace", "Lowercase", "Title case"],
    key="std_option"
)

if st.button("Apply Standardization"):

    df_copy = df.copy()

    if std_option == "Trim whitespace":
        df_copy[std_col] = df_copy[std_col].astype(str).str.strip()

    elif std_option == "Lowercase":
        df_copy[std_col] = df_copy[std_col].astype(str).str.lower()

    elif std_option == "Title case":
        df_copy[std_col] = df_copy[std_col].astype(str).str.title()

    st.session_state["df"] = df_copy

    st.success("✔ Standardization applied")
    st.rerun()


# =========================================================
# 2️⃣ MAPPING / REPLACEMENT
# =========================================================
st.markdown("### 🔁 Mapping / Replacement")

map_col = st.selectbox("Select column", cat_cols, key="map_col")

unique_vals = sorted(df[map_col].dropna().unique())
st.caption("Edit the 'New' column to map values (e.g. 'A+' → 'Positive')")
mapping_df = pd.DataFrame({
    "Original": unique_vals,
    "New": unique_vals
})

edited_map = st.data_editor(
    mapping_df,
    num_rows="fixed",
    use_container_width=True,
    key="mapping_editor"
)
keep_unmatched = st.checkbox(
    "Keep values not listed in mapping (otherwise → 'Other')",
    value=True
)
if st.button("Apply Mapping"):

    df_copy = df.copy()

    before = df[map_col].nunique()  

    mapping_dict = dict(zip(edited_map["Original"], edited_map["New"]))

    if keep_unmatched:
        df_copy[map_col] = df_copy[map_col].map(mapping_dict).fillna(df_copy[map_col])
    else:
        df_copy[map_col] = df_copy[map_col].map(mapping_dict).fillna("Other")

    after = df_copy[map_col].nunique()  
    if before == after:
        st.info("No changes detected. Modify mapping values.")

    st.session_state["df"] = df_copy

    st.success(f"✔ Mapping applied: {before} → {after} unique values")
    st.write("Preview after mapping:")
    st.dataframe(df_copy.head())

    st.write(f"Unique values: {before} → {after}")
    st.session_state["log"].append(
    f"Mapping → column '{map_col}' ({len(mapping_dict)} mappings)"
    )

    st.rerun()


# =====================================================
# 📉 RARE GROUPING & 🧠 ONE-HOT ENCODING
# =====================================================

st.markdown("## 📉 Rare Grouping & 🧠 One-hot Encoding")

# ✅ Always use session_state as source of truth
df = st.session_state["df"]

cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

if not cat_cols:
    st.info("No categorical columns available.")
    st.stop()

col = st.selectbox("Select categorical column", cat_cols, key="rg_col")

n_unique = df[col].nunique()

if n_unique <= 10:
    st.success(f"Safe to encode ({n_unique} categories)")
elif n_unique <= 20:
    st.warning(f"{n_unique} categories – encoding may add many columns")
else:
    st.error(f"{n_unique} unique values – not recommended. Consider grouping first.")# ------------------ RARE GROUPING ------------------

st.markdown("### 📉 Handle Rare Categories")

apply_grouping = st.checkbox("Group rare values into 'Other'", key="rg_check")

threshold = 1.0

if apply_grouping:
    threshold = st.slider(
        "Minimum frequency (%) to keep a category",
        0.0, 70.0, 1.0,
        key="rg_slider"
    )

    st.caption(
        "Categories appearing less than this percentage will be grouped into 'Other'. "
        "Example: 1% means values appearing in less than 1% of rows will be replaced."
    )

    # 📊 Distribution
    freq = df[col].value_counts(normalize=True) * 100
    freq = freq.sort_values()

    st.write("📊 Category distribution (%):")
    st.dataframe(freq.round(2), use_container_width=True)

    # 📊 Impact preview
    rare_count = (freq < threshold).sum()
    rare_percent = freq[freq < threshold].sum()

    if rare_count == 0:
        st.info("No categories fall below this threshold.")
    else:
        st.info(
            f"{rare_count} categories ({rare_percent:.2f}% of data) "
            f"will be grouped into 'Other'"
        )

# ------------------ ONE-HOT ENCODING ------------------

st.markdown("### 🧠 Convert to Machine-Friendly Format")

apply_ohe = st.checkbox(
    "Apply one-hot encoding",
    disabled=(n_unique > 30),
    key="ohe_check"
)
if n_unique > 30:
    st.warning(
        f"One-hot encoding disabled: '{col}' has {n_unique} unique values. "
        "Use rare grouping first."
    )
replace_original = st.checkbox(
    "Replace original column after encoding",
    value=True,
    key="replace_col"
)

# ------------------ APPLY ------------------

if st.button("Apply Changes", key="rg_ohe_btn"):

    df_copy = df.copy()

    before_cols = df_copy.shape[1]
    before_unique = df_copy[col].nunique() if col in df_copy.columns else "encoded"

    # ---------- STEP 1: GROUPING ----------
    if apply_grouping:
        freq = df_copy[col].value_counts(normalize=True) * 100
        rare_values = freq[freq < threshold]

        rare_category_count = len(rare_values)
        affected_rows_percent = rare_values.sum()

        if rare_category_count == 0:
            st.info("No categories fall below this threshold.")
        else:
            st.info(
                f"{rare_category_count} categories will be grouped into 'Other' "
                f"(affects {affected_rows_percent:.2f}% of rows)"
            )

        df_copy[col] = df_copy[col].apply(
            lambda x: "Other" if x in rare_values else x
        )

    # ---------- STEP 2: ENCODING ----------
    new_columns = []

    if apply_ohe:

        # 🔥 remove old encoded columns (prevents duplicates)
        existing_cols = [c for c in df_copy.columns if c.startswith(f"{col}_")]
        df_copy = df_copy.drop(columns=existing_cols, errors="ignore")

        dummies = pd.get_dummies(df_copy[col], prefix=col, dtype=int)
        new_columns = dummies.columns.tolist()

        if replace_original:
            df_copy = pd.concat(
                [df_copy.drop(columns=[col]), dummies],
                axis=1
            )
        else:
            df_copy = pd.concat([df_copy, dummies], axis=1)

        if existing_cols:
            st.info(f"Re-encoding '{col}' (old encoded columns replaced)")

    after_cols = df_copy.shape[1]
    after_unique = df_copy[col].nunique() if col in df_copy.columns else "encoded"

    # ---------- SAVE ----------
    st.session_state["df"] = df_copy

    # ---------- FEEDBACK ----------
    st.success("✔ Changes applied successfully")

    if apply_grouping:
        st.write(f"Grouped rare categories below {threshold}%")
        st.write(f"Unique values: {before_unique} → {after_unique}")

    if apply_ohe:
        st.write(f"Columns: {before_cols} → {after_cols}")
        st.write("New columns created:")
        st.write(new_columns)

    if not apply_grouping and not apply_ohe:
        st.info("No changes selected.")

    st.session_state["log"].append(
        f"One-hot encoding → {col} (new cols: {len(new_columns)})"
    )
    st.rerun()

st.markdown("---")
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
st.markdown(f"**Total rows:** {len(df)}")
st.markdown(f"**Outliers found ({outlier_method}):** {len(outliers)}")
if outlier_method == "IQR":
    st.markdown(f"**Lower bound:** {lower}")
    st.markdown(f"**Upper bound:** {upper}")
st.markdown(f"**Showing top 10 outliers (Total: {len(outliers)})**")

st.dataframe(outliers.head(10), width="stretch")

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
    st.dataframe(df[scale_cols].describe(), width="stretch")

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
    st.dataframe(df_copy[scale_cols].describe().round(3), width="stretch")
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

st.markdown("## 🧾 Transformation Log")

if st.session_state["log"]:
    for i, entry in enumerate(st.session_state["log"], 1):
        st.write(f"{i}. {entry}")
else:
    st.info("No transformations yet.")