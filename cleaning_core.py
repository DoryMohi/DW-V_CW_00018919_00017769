import streamlit as st
import pandas as pd
import numpy as np
from utils import add_log

# =====================================================
# 🧹 MISSING VALUES
# =====================================================
def missing_section(df, add_log):
    st.markdown("## Missing Values")

    missing = df.isnull().sum()

    missing_df = pd.DataFrame({
        "Missing Count": missing,
        "Missing %": ((missing / len(df)) * 100).round(2)
    })

    # ✅ FILTER ONLY columns with missing values
    missing_df = missing_df[missing_df["Missing Count"] > 0]
    missing_df = missing_df.sort_values(by="Missing Count", ascending=False)

    if missing_df.empty:
        st.success("✔ Dataset is clean. No missing values found.")
    else:
        st.dataframe(missing_df, use_container_width=True)

    # ✅ SORT (optional but nice)
    total_missing = missing.sum()

    st.metric("Total Missing Values", total_missing)
# ------------------ DROP BY THRESHOLD ------------------
    st.markdown("### 🚫 Drop Columns by Missing %")

    # init
    if "threshold" not in st.session_state:
        st.session_state.threshold = 5.0

    def update_from_input():
        st.session_state.threshold = st.session_state.input_val
        st.session_state.slider_val = st.session_state.input_val
        st.rerun()


    def update_from_slider():
        st.session_state.threshold = st.session_state.slider_val
        st.session_state.input_val = st.session_state.slider_val

    col1, col2 = st.columns([3, 1])

    with col1:
        st.slider(
            "Missing value threshold (%)",
            0.0, 100.0,
            step=0.1,
            key="slider_val",
            on_change=update_from_slider
        )

    with col2:
        st.number_input(
            "Value",
            0.0, 100.0,
            step=0.1,
            key="input_val",
            on_change=update_from_input
        )

    threshold = st.session_state.threshold
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
    disable_button = len(cols_to_drop) == 0

    if st.button("🗑️ Apply Column Drop", type="primary", disabled=disable_button):
            st.session_state["history"].append(df.copy())
            df_copy = df.copy()
            before_cols = len(df.columns)

            df_copy = df_copy.drop(columns=cols_to_drop)

            after_cols = len(df_copy.columns)

            st.session_state["df"] = df_copy

            if "log" in st.session_state:
                add_log(
                    operation="Drop Columns (Missing)",
                    columns=", ".join(cols_to_drop),
                    method=f">{threshold}%",
                    action="Columns removed",
                    affected=len(cols_to_drop),
                    details=f"{before_cols} → {after_cols}"
                )

            st.success("✔ Columns dropped!")
            st.markdown(f"**Columns before:** {before_cols}")
            st.markdown(f"**Columns after:** {after_cols}")

            st.rerun()

    st.markdown("---")


 # ------------------ HANDLE MISSING ------------------
    st.markdown("### ⚙️ Handle Missing Values")

    # get only columns with missing values
    missing_columns = df.columns[df.isnull().sum() > 0].tolist()

    # 🚫 EARLY EXIT (IMPORTANT)
    if not missing_columns:
        st.success("✔ No columns have missing values. Nothing to handle.")
    else:
        col1, col2 = st.columns(2)

        # ------------------ COLUMN SELECT ------------------
        with col1:
            missing_col = st.selectbox("Column", missing_columns)

            # ✅ reset preview when column changes
            if "last_column" not in st.session_state:
                st.session_state["last_column"] = missing_col

            if st.session_state["last_column"] != missing_col:
                st.session_state["preview_ready"] = False
                st.session_state["last_column"] = missing_col

            missing_count = df[missing_col].isnull().sum()
            missing_percent = (missing_count / len(df)) * 100

            st.caption(f"Missing: {missing_count} ({missing_percent:.2f}%)")

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
                "Fill with most frequent",
                "Fill with constant",
                "Forward fill",
                "Backward fill"
            ]
        with col2:
            missing_action = st.selectbox("Action", actions, key="missing_action")

            # ✅ reset preview when action changes
            if "last_action" not in st.session_state:
                st.session_state["last_action"] = missing_action

            if st.session_state["last_action"] != missing_action:
                st.session_state["preview_ready"] = False
                st.session_state["last_action"] = missing_action

            value = None
            if missing_action == "Fill with constant":
                value = st.text_input("Enter value")

            disable_apply = missing_count == 0

            # ✅ Show info only BEFORE apply
            if not st.session_state.get("preview_ready", False):
                if missing_action == "Fill with mean":
                    st.info("Missing values will be replaced with mean")
                elif missing_action == "Fill with median":
                    st.info("Missing values will be replaced with median")
                elif missing_action in ["Fill with mode", "Fill with most frequent"]:
                    st.info("Missing values will be replaced with the most frequent value")
                elif missing_action == "Forward fill":
                    st.info("Missing values will be filled using previous row values")
                elif missing_action == "Backward fill":
                    st.info("Missing values will be filled using next row values")
                elif missing_action == "Drop rows":
                    st.warning("Rows with missing values will be removed permanently")            
                    
                    
                    # ------------------ APPLY ------------------
            if st.button("Apply Changes", disabled=disable_apply):
                before_missing = df[missing_col].isnull().sum()
                before_rows = len(df)

                st.session_state["history"].append(df.copy())

                try:
                    df_copy = df.copy()

                    # ===== APPLY LOGIC =====
                    if missing_action == "Drop rows":
                        df_copy = df_copy.dropna(subset=[missing_col])

                    elif missing_action == "Fill with mean":
                        mean_val = df_copy[missing_col].mean()
                        if pd.api.types.is_integer_dtype(df_copy[missing_col]):
                            mean_val = int(round(mean_val))
                        df_copy[missing_col] = df_copy[missing_col].fillna(mean_val)

                    elif missing_action == "Fill with median":
                        median_val = df_copy[missing_col].median()
                        if pd.api.types.is_integer_dtype(df_copy[missing_col]):
                            median_val = int(round(median_val))
                        df_copy[missing_col] = df_copy[missing_col].fillna(median_val)

                    elif missing_action in ["Fill with mode", "Fill with most frequent"]:
                        mode_series = df_copy[missing_col].mode()
                        if not mode_series.empty:
                            df_copy[missing_col] = df_copy[missing_col].fillna(mode_series[0])

                    elif missing_action == "Fill with constant":
                        if value is None or value == "":
                            st.warning("Please enter a value.")
                            st.stop()

                        df_copy[missing_col] = df_copy[missing_col].replace(
                            ["", " ", "NA", "None"], np.nan
                        )

                        if is_numeric:
                            try:
                                value = float(value)
                            except:
                                st.error("Enter a valid number.")
                                st.stop()

                        df_copy[missing_col] = df_copy[missing_col].fillna(value)

                    elif missing_action == "Forward fill":
                        df_copy[missing_col] = df_copy[missing_col].ffill()

                    elif missing_action == "Backward fill":
                        df_copy[missing_col] = df_copy[missing_col].bfill()

                    # ===== SAVE =====
                    after_missing = df_copy[missing_col].isnull().sum()
                    after_rows = len(df_copy)

                    st.session_state["df"] = df_copy
                    st.session_state["preview"] = {
                        "column": missing_col,
                        "action": missing_action,
                        "before_missing": before_missing,
                        "after_missing": after_missing,
                        "before_rows": before_rows,
                        "after_rows": after_rows
                    }

                    st.session_state["preview_ready"] = True

                    st.success("✔ Operation applied")

                except Exception as e:
                    st.error(f"Error: {e}")

        # ------------------ PREVIEW ------------------
        if (
            st.session_state.get("preview_ready")
            and "history" in st.session_state
            and len(st.session_state["history"]) > 0
            and "preview" in st.session_state
        ):
            p = st.session_state["preview"]
            prev_df = st.session_state["history"][-1]

            if p["column"] in prev_df.columns:
                mask = prev_df[p["column"]].isnull()

                before_df = prev_df.loc[mask, [p["column"]]]
                after_df = st.session_state["df"].loc[mask, [p["column"]]]

                st.markdown("### 🔍 Data Preview")

                col_b, col_a = st.columns(2)

                with col_b:
                    st.markdown("**Before (affected rows)**")
                    if before_df.empty:
                        st.info("No affected rows.")
                    else:
                        st.dataframe(before_df.head(10))

                with col_a:
                    st.markdown("**After (affected rows)**")
                    if after_df.empty:
                        if p.get("action") == "Drop rows":
                            st.info("Rows with missing values were removed.")
                        else:
                            st.info("No affected rows.")
                    else:
                        st.dataframe(after_df.head(10))

st.markdown("---")
def duplicates_section(df, add_log):
    st.markdown("## 🔁 Duplicates")

    dup_type = st.radio(
        "Duplicate type",
        ["Full row duplicates", "Subset duplicates"],
        index=0
    )

    if "last_dup_type" not in st.session_state:
        st.session_state["last_dup_type"] = dup_type

    if st.session_state["last_dup_type"] != dup_type:
        st.session_state["dup_applied"] = False
        st.session_state["last_dup_type"] = dup_type

    subset_cols = []

    # ---- LOGIC ----
    if dup_type == "Subset duplicates":
        subset_cols = st.multiselect("Select columns", df.columns)

        if "last_subset" not in st.session_state:
            st.session_state["last_subset"] = subset_cols

        if st.session_state["last_subset"] != subset_cols:
            st.session_state["dup_applied"] = False
            st.session_state["last_subset"] = subset_cols

        if not subset_cols:
            st.warning("Select at least one column to detect duplicates.")
            duplicates = pd.DataFrame()
        else:
            duplicates = df[df.duplicated(subset=subset_cols, keep=False)]
            duplicates = duplicates.sort_values(by=subset_cols)

    else:
        duplicates = df[df.duplicated(keep=False)]
        duplicates = duplicates.sort_values(by=df.columns.tolist())

    # ---- SHOW DUPLICATES ----
    dup_groups = duplicates.drop_duplicates(
        subset=subset_cols if len(subset_cols) > 0 else None
    )

    st.write(f"Duplicate rows: {len(duplicates)}")
    st.write(f"Duplicate groups: {len(dup_groups)}")

    if not duplicates.empty:
        st.dataframe(duplicates, width="stretch")
    else:
        if dup_type == "Subset duplicates" and not subset_cols:
            pass  # don't confuse user
        else:
            st.info("No duplicates found.")

    # ---- ACTION ----
    if duplicates.empty:
        st.session_state["dup_applied"] = False
    else:
        dup_action = st.selectbox(
            "Action",
            ["Do nothing", "Remove duplicates (keep first)", "Remove duplicates (keep last)"]
        )
    # ---- APPLY ----
    
        disabled = duplicates.empty or dup_action == "Do nothing"

        if st.button("Apply Duplicate Operation", disabled=disabled):
            st.session_state["history"].append(df.copy())
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

            if dup_action == "Do nothing":
                st.info("No changes applied.")
            elif removed == 0:
                st.info("No duplicates to remove.")
            else:
                st.success("✔ Duplicates removed")
            add_log(
                operation="Duplicates",
                columns=subset_cols if subset_cols else "All",
                method=dup_type,
                action=dup_action,
                affected=removed,
                details=f"{before_rows} → {after_rows} rows"
            )

            st.rerun()

    # ---- RESULT ----
    if (
        "dup_preview" in st.session_state
        and st.session_state.get("dup_applied")
        and st.session_state["dup_preview"]["removed"] > 0
    ):
        p = st.session_state["dup_preview"]

        # Only show result if something actually changed
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

def types_section(df, add_log):
    st.markdown("## 🧩 Data Types & Parsing")

    df = st.session_state["df"]

    # -------- SELECT COLUMN --------
    type_col = st.selectbox("Select column to convert", df.columns, key="type_col")

    # Clean sample for detection
    sample_values = (
        df[type_col]
        .replace(["None", "none", "NA", "N/A", "", " "], pd.NA)
        .dropna()
        .astype(str)
        .head(20)
    )

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

    # -------- OPTIONS --------
    parse_mode = None
    date_format = None
    clean_numeric = False

    if target_type == "Datetime":
        parse_mode = st.radio(
            "Parsing mode",
            ["Auto parse", "Specify format"]
        )

        if parse_mode == "Specify format":
            date_formats = {
                "YYYY-MM-DD (2024-03-27)": "%Y-%m-%d",
                "DD-MM-YYYY (27-03-2024)": "%d-%m-%Y",
                "MM-DD-YYYY (03-27-2024)": "%m-%d-%Y",
                "DD/MM/YYYY (27/03/2024)": "%d/%m/%Y",
                "MM/DD/YYYY (03/27/2024)": "%m/%d/%Y",
                "27 Mar 2024": "%d %b %Y"
            }

            selected_label = st.selectbox(
                "Select datetime format",
                list(date_formats.keys())
            )
            date_format = date_formats[selected_label]

    if str(current_type).startswith("datetime") and target_type == "Numeric":
        st.error("Cannot convert datetime to numeric.")

    if target_type == "Numeric":
        clean_numeric = st.checkbox("Clean dirty values (remove $, commas)")

    # -------- CURRENT TYPE --------
    st.markdown(f"**Current type:** `{current_type}`")

    # -------- DISABLE LOGIC --------
    disabled = False

    if target_type == "Datetime" and str(current_type).startswith("datetime"):
        disabled = True

    if target_type == "Numeric" and ("int" in str(current_type) or "float" in str(current_type)):
        disabled = True

    # -------- APPLY --------
    if st.button("Apply Type Conversion", disabled=disabled):

        st.session_state["history"].append(df.copy())

        df_copy = df.copy()

        # ✅ CLEAN FIRST (IMPORTANT FIX)
        df_copy[type_col] = df_copy[type_col].replace(
            ["None", "none", "NA", "N/A", "", " "],
            pd.NA
        )

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
                    parsed = pd.to_datetime(
                        df_copy[type_col],
                        format=date_format,
                        errors="coerce",
                        exact=False
                    )
                    if parsed.notna().mean() < 0.5:
                        parsed = pd.to_datetime(
                            df_copy[type_col],
                            errors="coerce",
                            format="mixed"
                        )

                else:
                    parsed = pd.to_datetime(
                        df_copy[type_col],
                        errors="coerce",
                        format="mixed"
                    )

                # ❗ IMPORTANT: only apply if parsing worked
                success_ratio = parsed.notna().mean()

                if success_ratio > 0.5:
                    df_copy[type_col] = parsed
                    if parse_mode == "Specify format" and date_format:
                        df_copy[type_col] = df_copy[type_col].dt.strftime(date_format)
                
                else:
                    st.error("Could not parse this column reliably.")

                    # Optional formatting
            

            after_type = df_copy[type_col].dtype
            after_na = df_copy[type_col].isna().sum()

            # -------- SAVE --------
            st.session_state["df"] = df_copy

            # -------- LOG --------
            add_log(
                operation="Type Conversion",
                columns=type_col,
                method=target_type,
                action="Converted",
                affected=len(df_copy),
                details=f"{before_type} → {after_type}, NaN: {before_na} → {after_na}"
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

            st.rerun()

        except Exception as e:
            st.error(f"Error: {e}")

    st.markdown("---")
def categorical_section(df, add_log):
    st.markdown("## 🏷️ Categorical Data Tools")

    df = st.session_state["df"]
    cat_cols = df.select_dtypes(include=["object", "category", "string"]).columns
    if len(cat_cols) == 0:
        st.info("No categorical columns available.")
    else:

        # =========================================================
        # 1️⃣ VALUE STANDARDIZATION
        # =========================================================
        st.markdown("### 🔧 Value Standardization")

        std_col = st.selectbox("Select column", cat_cols, key="std_col")

        std_option = st.selectbox(
            "Choose standardization",
            ["Trim whitespace", "Lowercase", "Title case", "UPPERCASE"],
            key="std_option"
        )

        if st.button("Apply Standardization"):
            st.session_state["history"].append(df.copy())

            df_copy = df.copy()

            before_values = df_copy[std_col].astype(str)

            # APPLY
            if std_option == "Trim whitespace":
                df_copy[std_col] = df_copy[std_col].astype(str).str.strip()

            elif std_option == "Lowercase":
                df_copy[std_col] = df_copy[std_col].astype(str).str.lower()

            elif std_option == "Title case":
                df_copy[std_col] = df_copy[std_col].astype(str).str.title()

            elif std_option == "UPPERCASE":
                df_copy[std_col] = df_copy[std_col].astype(str).str.upper()
            after_values = df_copy[std_col].astype(str)

            changed = (before_values != after_values).sum()

            # SAVE DATA
            st.session_state["df"] = df_copy

            # ✅ SAVE RESULT (THIS WAS MISSING)
            st.session_state["std_result"] = {
                "before": before_values.head(5),
                "after": after_values.head(5),
                "changed": int(changed),
                "applied": True
            }

            # ✅ FEEDBACK
        if st.session_state.get("std_result", {}).get("applied"):

            r = st.session_state["std_result"]

            if r["changed"] == 0:
                st.info("No values were changed.")
            else:
                st.success("✔ Standardization applied")

                st.markdown("### 🔍 Result")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Before**")
                    st.dataframe(r["before"], use_container_width=True)

                with col2:
                    st.markdown("**After**")
                    st.dataframe(r["after"], use_container_width=True)

                st.write(f"Changed values: {r['changed']}")
        st.markdown("---")

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
            st.session_state["history"].append(df.copy())

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
            add_log(
                operation="Mapping",
                columns=map_col,
                method="Value mapping",
                action="Values replaced",
                affected=before - after,
                details=f"{before} → {after} unique"
            )

            st.rerun()

        st.markdown("---")

    # =====================================================
    # 📉 RARE GROUPING & 🧠 ONE-HOT ENCODING
    # =====================================================

    st.markdown("## 📉 Rare Grouping & One-hot Encoding")

    df = st.session_state["df"]

    cat_cols = [
        col for col in df.select_dtypes(include=["object", "category", "string"]).columns
        if df[col].nunique() <= 30
    ]

    if not cat_cols:
        st.info("No categorical columns available.")

    else:
        col = st.selectbox("Select categorical column", cat_cols, key="rg_col")

        # 🔥 CLEAR RESULT WHEN COLUMN CHANGES
        if "last_rg_col" not in st.session_state:
            st.session_state["last_rg_col"] = col

        if st.session_state["last_rg_col"] != col:
            st.session_state.pop("ohe_result", None)
            st.session_state["last_rg_col"] = col

        n_unique = df[col].nunique()

        if n_unique > 30:
            st.warning(f"{n_unique} categories → encoding may create too many columns")
        elif n_unique <= 10:
            st.success(f"Good choice ({n_unique} categories)")

        # ------------------ RARE GROUPING ------------------

        st.markdown("### 📉 Handle Rare Categories")

        apply_grouping = st.checkbox("Group rare values into 'Other'", key="rg_check")

        if apply_grouping:

            # INIT
            if "rg_threshold" not in st.session_state:
                st.session_state.rg_threshold = 1.0
                st.session_state.rg_slider = 1.0
                st.session_state.rg_input = 1.0

            def update_rg_from_input():
                st.session_state.rg_threshold = st.session_state.rg_input
                st.session_state.rg_slider = st.session_state.rg_input
                st.rerun()

            def update_rg_from_slider():
                st.session_state.rg_threshold = st.session_state.rg_slider
                st.session_state.rg_input = st.session_state.rg_slider

            col1, col2 = st.columns([3, 1])

            with col1:
                st.slider(
                    "Minimum frequency (%) to keep a category",
                    0.0, 70.0,
                    step=0.1,
                    key="rg_slider",
                    on_change=update_rg_from_slider
                )

            with col2:
                st.number_input(
                    "Value",
                    0.0, 70.0,
                    step=0.1,
                    key="rg_input",
                    on_change=update_rg_from_input
                )

            threshold = st.session_state.rg_threshold

            # 👇 EXPLANATION
            st.caption(
                "Categories appearing in less than this percentage will be grouped into 'Other'."
            )

                        # 📊 ORIGINAL DISTRIBUTION
            counts = df[col].value_counts()
            freq = (counts / len(df)) * 100

            # 🎯 CREATE DYNAMIC GROUPING
            grouped_labels = freq.index.to_series().apply(
                lambda x: "Other" if freq[x] < threshold else x
            )

            # 🧠 BUILD FINAL TABLE
            final_df = pd.DataFrame({
                "Category": freq.index,
                "Percentage (%)": freq.values.round(2),
                "Count": counts.values,
                "After Grouping": grouped_labels.values
            })

            # optional: sort nicely
            final_df = final_df.sort_values(by="Percentage (%)", ascending=False)

            # 🎨 DISPLAY
            st.markdown("### 📊 Category Distribution & Grouping")
            st.dataframe(final_df, use_container_width=True)

            # 📢 INFO MESSAGE
            rare_count = (freq < threshold).sum()
            rare_percent = freq[freq < threshold].sum()

            if rare_count == 0:
                st.info("No categories fall below this threshold.")
            else:
                st.info(
                    f"{rare_count} categories ({rare_percent:.2f}% of data) will be grouped into 'Other'"
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

            # 🔥 CLEAR OLD RESULT
            st.session_state.pop("ohe_result", None)

            st.session_state["history"].append(df.copy())

            df_copy = df.copy()

            before_cols = df_copy.shape[1]

            # ---------- GROUPING ----------
            if apply_grouping:
                freq = df_copy[col].value_counts(normalize=True) * 100
                rare_values = freq[freq < threshold]

                df_copy[col] = df_copy[col].apply(
                    lambda x: "Other" if x in rare_values else x
                )

            # ---------- ENCODING ----------
            new_columns = []

            if apply_ohe:
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

            after_cols = df_copy.shape[1]

            st.session_state["df"] = df_copy

            # ✅ SAVE RESULT
            st.session_state["ohe_result"] = {
                "before_cols": before_cols,
                "after_cols": after_cols,
                "new_cols": new_columns,
                "removed_col": col if (apply_ohe and replace_original) else None,
                "preview": df_copy.head(5)
            }

            add_log(
                operation="Encoding",
                columns=col,
                method="One-hot",
                action="Encoded categories",
                affected=len(new_columns),
                details=f"{before_cols} → {after_cols} columns"
            )

        

    # ------------------ RESULT ------------------

        if "ohe_result" in st.session_state:

            r = st.session_state["ohe_result"]

            st.markdown("### 🔍 Result")
            st.caption("Last operation result")

            st.write(f"Columns before: {r['before_cols']}")
            st.write(f"Columns after: {r['after_cols']}")
            st.write(f"New columns created: {len(r['new_cols'])}")

            if r["removed_col"]:
                st.write(f"Original column removed: {r['removed_col']}")

            if r["new_cols"]:
                st.markdown("**New columns:**")
                st.dataframe(
                    pd.DataFrame(r["new_cols"], columns=["Column Name"]),
                    use_container_width=True
                )

            st.markdown("**Preview:**")
            st.dataframe(r["preview"], use_container_width=True)

            # optional manual clear
            if st.button("Clear result"):
                st.session_state.pop("ohe_result", None)
                

    st.markdown("---")
    
def outliers_section(df, add_log):
    st.markdown("## Outlier Detection & Handling")
    st.caption("Detect and handle extreme values that may distort your analysis.")

    all_num_cols = df.select_dtypes(include=["int64", "float64"]).columns
    num_cols = [col for col in all_num_cols if df[col].nunique() > 5]

    if len(num_cols) == 0:
        st.info("No numeric columns available.")
    else:

        # ------------------ CONFIGURATION ------------------
        st.markdown("### ⚙️ Configure")

        col1, col2, col3 = st.columns(3)

        with col1:
            out_col = st.selectbox("Column", num_cols, key="outlier_col")

        with col2:
            outlier_method = st.selectbox(
                "Method",
                ["IQR", "Z-score"],
                help="IQR = robust for skewed data. Z-score = assumes normal distribution.",
                key="outlier_method"
            )

        with col3:
            outlier_action = st.selectbox(
                "Action",
                ["Do nothing", "Cap (Winsorize)", "Remove outliers"],
                help="Choose how to handle detected outliers.",
                key="outlier_action"
            )

        # ------------------ DETECTION ------------------
        if outlier_method == "IQR":
            Q1 = df[out_col].quantile(0.25)
            Q3 = df[out_col].quantile(0.75)
            IQR = Q3 - Q1

            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR

            outliers = df[(df[out_col] < lower) | (df[out_col] > upper)]

        elif outlier_method == "Z-score":
            std = df[out_col].std()
            st.caption("Z-score threshold: |z| > 3")

            if std == 0:
                st.warning("Standard deviation is 0. Cannot compute Z-score.")
                outliers = df.iloc[0:0]
                lower, upper = None, None
            else:
                z_scores = (df[out_col] - df[out_col].mean()) / std
                outliers = df[np.abs(z_scores) > 3]
                lower, upper = None, None

        # ------------------ SUMMARY ------------------
        st.markdown("### 📊 Detection Summary")

        col1, col2 = st.columns(2)

        total_rows = len(df)
        outlier_count = len(outliers)

        col1.metric("Total rows", total_rows)
        col2.metric("Outliers found", outlier_count)

        # ---- STATUS MESSAGE ----
        if outlier_count == 0:
            st.success("✔ No outliers detected. This column looks clean.")
        else:
            if outlier_count < 10:
                st.info("Small number of outliers detected. Safe to handle.")
            else:
                st.warning("Many outliers detected. Consider cleaning.")

        # ---- SHOW BOUNDS ONLY IF USEFUL ----
        if outlier_method == "IQR" and outlier_count > 0:
            st.caption(f"IQR bounds: [{lower:,.2f}, {upper:,.2f}]")

        # ------------------ PREVIEW + ACTION ------------------
        if outlier_count > 0:

            st.markdown("### 🔍 Preview")
            st.dataframe(outliers.head(10), use_container_width=True)

            # ---- ACTION INFO ----
            if outlier_action == "Remove outliers":
                st.warning(f"{outlier_count} rows will be removed")
            elif outlier_action == "Cap (Winsorize)":
                st.info(f"{outlier_count} values will be capped")

            # ---- APPLY BUTTON ----
            if outlier_action != "Do nothing":
                if st.button("Apply Outlier Operation", type="primary", use_container_width=True):
                    st.session_state["history"].append(df.copy())

                    df_copy = df.copy()
                    before_rows = len(df)

                    if outlier_action == "Remove outliers":

                        if outlier_method == "IQR":
                            df_copy = df_copy[
                                (df_copy[out_col] >= lower) &
                                (df_copy[out_col] <= upper)
                            ]

                        elif outlier_method == "Z-score":
                            std = df_copy[out_col].std()
                            if std != 0:
                                z_scores = (df_copy[out_col] - df_copy[out_col].mean()) / std
                                df_copy = df_copy[np.abs(z_scores) <= 3]

                        removed = before_rows - len(df_copy)
                        affected = removed
                        st.write(f"Rows removed: {removed}")

                    elif outlier_action == "Cap (Winsorize)":

                        if outlier_method == "IQR":
                            before_values = df_copy[out_col].copy()
                            df_copy[out_col] = df_copy[out_col].clip(lower, upper)
                            affected = (before_values != df_copy[out_col]).sum()
                            st.write(f"Values capped: {affected}")
                        else:
                            st.warning("Capping not supported for Z-score")
                            affected = 0

                    add_log(
                        operation="Outliers",
                        columns=out_col,
                        method=outlier_method,
                        action=outlier_action,
                        affected=int(affected),
                        details=f"{before_rows} → {len(df_copy)} rows"
                    )

                    st.session_state["df"] = df_copy
                    st.success("Changes applied!")
                    st.rerun()

    st.markdown("---")
