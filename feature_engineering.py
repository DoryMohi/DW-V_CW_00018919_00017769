import streamlit as st
import pandas as pd
import numpy as np
from utils import add_log

def feature_engineering_section(df, add_log):
    st.markdown("## ⚙️ Feature Engineering")

    st.subheader("Normalization / Scaling")

    df = df.copy()

    num_cols = df.select_dtypes(include=["int64", "float64"]).columns

    if len(num_cols) == 0:
        st.info("No numeric columns available.")
    else:
        scale_cols = st.multiselect("Select columns to scale", num_cols)

        scaling_method = st.selectbox(
            "Scaling method",
            ["Min-Max", "Z-score"],
            key="scaling_method"
        )
        if scaling_method == "Min-Max":
            st.caption("Scales values to range [0, 1]")
        elif scaling_method == "Z-score":
            st.caption("Standardizes values (mean ≈ 0, std ≈ 1)")
        # ------------------ BEFORE ------------------
        if scale_cols:
            st.markdown("### 📊 Before Scaling")
            st.dataframe(df[scale_cols].describe().round(3), use_container_width=True)

        # ------------------ APPLY ------------------
        if st.button("Apply Scaling", type="primary"):

            df_copy = df.copy()

            # STORE BEFORE
            before_stats = df[scale_cols].describe().round(3)

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

            # STORE AFTER
            after_stats = df_copy[scale_cols].describe().round(3)

            # SAVE
            st.session_state["df"] = df_copy

            # SHOW COMPARISON (IMMEDIATELY)
            st.markdown("### 🔍 Before vs After")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Before**")
                st.dataframe(before_stats, use_container_width=True)

            with col2:
                st.markdown("**After**")
                st.dataframe(after_stats, use_container_width=True)

            st.success("Scaling applied!")
            st.caption(f"{len(scale_cols)} columns scaled using {scaling_method}")
            # ------------------ LOG ------------------
            affected = len(df) * len(scale_cols)

            add_log(
                operation="Scaling",
                columns=", ".join(scale_cols),
                method=scaling_method,
                action="Scaled values",
                affected=affected,
                details="Normalization applied"
            )


    st.markdown("---")
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

        elif new_name in df.columns:
            st.warning("Column name already exists.")

        elif rename_col == new_name:
            st.info("New name is the same as the old one.")

        else:
            df_copy = df.copy()
            df_copy = df_copy.rename(columns={rename_col: new_name})

            st.session_state["df"] = df_copy

            st.success(f"Column renamed: '{rename_col}' → '{new_name}'")

    st.markdown("---")
    st.subheader("Drop Columns")

    drop_cols = st.multiselect("Select columns to drop", df.columns)

    if st.button("Drop Selected Columns"):
        if not drop_cols:
            st.warning("Select at least one column.")

        else:
            df_copy = df.copy()
            before = len(df_copy.columns)

            df_copy = df_copy.drop(columns=drop_cols)
            after = len(df_copy.columns)

            removed = before - after

            if removed == 0:
                st.info("No columns were removed.")
            else:
                st.success(f"{removed} column(s) removed.")

            st.session_state["df"] = df_copy

            add_log(
                operation="Drop Columns",
                columns=", ".join(drop_cols),
                method="Manual",
                action="Columns removed",
                affected=removed,
                details=f"{before} → {after}"
            )
            st.session_state["df"] = df_copy


    st.markdown("---")

    st.subheader("Create New Column")

    num_cols = df.select_dtypes(include=["int64", "float64"]).columns

    if len(num_cols) < 1:
        st.warning("No numeric columns available.")
    else:
        new_col_name = st.text_input("New column name")

        formula_type = st.selectbox(
            "Select formula",
            ["Addition", "Subtraction", "Division", "Log", "Mean Difference"]
        )

        col1 = st.selectbox("Column 1", num_cols)

        if formula_type in ["Addition", "Subtraction", "Division"]:
            if len(num_cols) < 2:
                st.warning("Need at least 2 numeric columns.")

            col2_options = [c for c in num_cols if c != col1]
            col2 = st.selectbox("Column 2", col2_options)
        else:
            col2 = None


    if st.button("Create Column"):
        if not new_col_name.strip():
            st.warning("Enter column name.")

        elif new_col_name in df.columns:
            st.warning("Column already exists.")

        else:
            df_copy = df.copy()

            try:
                if formula_type == "Division":
                    if (df_copy[col2] == 0).any():
                        st.warning("Division by zero detected. Replacing with NaN.")                        

                # Apply formula
                if formula_type == "Addition":
                    df_copy[new_col_name] = df_copy[col1] + df_copy[col2]

                elif formula_type == "Subtraction":
                    df_copy[new_col_name] = df_copy[col1] - df_copy[col2]

                elif formula_type == "Division":
                    df_copy[new_col_name] = df_copy[col1] / df_copy[col2]

                elif formula_type == "Log":
                    df_copy[new_col_name] = np.log(df_copy[col1].clip(lower=1e-9))

                elif formula_type == "Mean Difference":
                    df_copy[new_col_name] = df_copy[col1] - df_copy[col1].mean()

                st.session_state["df"] = df_copy

                st.success(f"Column '{new_col_name}' created successfully")

                add_log(
                    operation="Feature Engineering",
                    columns=new_col_name,
                    method=formula_type,
                    action="New column created",
                    affected=len(df_copy),
                    details=f"Based on {col1}" + (f" & {col2}" if col2 else "")
                )
                st.markdown("### Preview")
                st.dataframe(
                    df_copy[[new_col_name]].reset_index(drop=True),
                    hide_index=True
                )

            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("---")

    st.subheader("Binning (Discretization)")

    num_cols = df.select_dtypes(include=["int64", "float64"]).columns

    if len(num_cols) == 0:
        st.warning("No numeric columns available.")
    else:
        bin_col = st.selectbox("Select numeric column", num_cols)

        bins = st.number_input("Number of bins", min_value=2, max_value=50, value=4)

        bin_method = st.selectbox(
            "Binning method",
            ["Equal Width", "Quantile"]
        )
        st.caption(
        "Equal Width → equal ranges (good for interpretation)\n"
        "Quantile → equal data per group (good for modeling)"
        )
        new_bin_col = st.text_input("New binned column name")

    if st.button("Apply Binning"):
        if not new_bin_col.strip():
            st.warning("Enter a name for new column.")

        elif new_bin_col in df.columns:
            st.warning("Column already exists.")

        else:
            df_copy = df.copy()

            try:
                # ✅ IMPORTANT: remove NaN BEFORE binning
                series = df_copy[bin_col].dropna()

                if series.nunique() < bins:
                    st.warning("Not enough unique values for this number of bins.")
                else:
                    if bin_method == "Equal Width":
                        binned = pd.cut(series, bins=bins)

                    elif bin_method == "Quantile":
                        binned = pd.qcut(
                            series,
                            q=bins,
                            duplicates="drop"
                        )

                    # ✅ assign back (preserve NaN positions)
                    df_copy[new_bin_col] = pd.Series(index=df_copy.index, dtype="object")
                    df_copy.loc[series.index, new_bin_col] = binned.astype(str)
                    df_copy[new_bin_col] = df_copy[new_bin_col].fillna("Missing")


                    st.session_state["df"] = df_copy

                    st.success(f"Binning applied on '{bin_col}'")
                    add_log(
                        operation="Binning",
                        columns=bin_col,
                        method=bin_method,
                        action="Discretized",
                        affected=len(df_copy),
                        details=f"{bins} bins → {new_bin_col}"
                    )
                    st.markdown("### Distribution")
                    st.dataframe(
                        df_copy[new_bin_col].value_counts(dropna=False).to_frame("Count"),
                        use_container_width=True
                    )
                    if df_copy[new_bin_col].isna().sum() > 0:
                        st.caption("⚠️ Some values could not be binned due to missing data")
                
            except Exception as e:
                st.error(f"Error: {e}")
    st.markdown("---")
