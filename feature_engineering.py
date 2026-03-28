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
        return

    scale_cols = st.multiselect("Select columns to scale", num_cols)

    if "prev_scale_cols" not in st.session_state:
        st.session_state["prev_scale_cols"] = scale_cols

    if scale_cols != st.session_state["prev_scale_cols"]:
        st.session_state["scaling_applied"] = False
        st.session_state["prev_scale_cols"] = scale_cols

    scaling_method = st.selectbox(
        "Scaling method",
        ["Min-Max", "Z-score"],
        key="scaling_method"
    )

    if scaling_method == "Min-Max":
        st.caption("Scales values to range [0, 1]")
    else:
        st.caption("Standardizes values (mean ≈ 0, std ≈ 1)")

    # ------------------ BEFORE ------------------
    if scale_cols and not st.session_state.get("scaling_applied", False):
        st.markdown("### 📊 Before Scaling")
        st.dataframe(df[scale_cols].describe().round(3), use_container_width=True)
    # ------------------ APPLY ------------------
    if st.button("Apply Scaling", type="primary"):
        st.session_state["history"].append(df.copy())
        st.session_state["scaling_applied"] = True

        df_copy = df.copy()

        # STORE BEFORE
        before_stats = df[scale_cols].describe().round(3)

        for col in scale_cols:

            # 🔥 FIX: force float
            df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce").astype(float)

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
        after_stats = df_copy[scale_cols].describe()

        # SAVE EVERYTHING
        st.session_state["df"] = df_copy
        st.session_state["scaling_result"] = {
            "before": before_stats,
            "after": after_stats,
            "cols": scale_cols,
            "method": scaling_method
        }

        # ------------------ RESULT ------------------
    if st.session_state.get("scaling_applied") and "scaling_result" in st.session_state:

        r = st.session_state["scaling_result"]

        st.markdown("### 🔍 Before vs After")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Before**")
            st.dataframe(r["before"], use_container_width=True)

        with col2:
            st.markdown("**After**")
            st.dataframe(r["after"].style.format("{:.4f}"), use_container_width=True)

        st.success("Scaling applied!")
        st.caption(f"{len(r['cols'])} columns scaled using {r['method']}")
        # LOG
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
        st.session_state["history"].append(df.copy())
        if new_name.strip() == "":
            st.warning("Enter a valid name.")

        elif new_name in df.columns:
            st.warning("Column name already exists.")

        elif rename_col == new_name:
            st.info("New name is the same as the old one.")

        else:
            df_copy = df.copy()
            df_copy = df_copy.rename(columns={rename_col: new_name})

            # SAVE DATA
            st.session_state["df"] = df_copy

            # 🔥 SAVE RESULT
            st.session_state["rename_result"] = {
                "old": rename_col,
                "new": new_name,
                "before": df.head(5),
                "after": df_copy.head(5)
            }
        if "rename_result" in st.session_state:

            r = st.session_state["rename_result"]

            st.info(f"Column '{r['old']}' has been renamed to '{r['new']}'")

            st.markdown("### 🔍 Preview")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Before**")
                st.dataframe(r["before"], use_container_width=True)

            with col2:
                st.markdown("**After**")
                st.dataframe(r["after"], use_container_width=True)

            # optional cleanup button
            if st.button("Clear result"):
                st.session_state["history"].append(df.copy())
                st.session_state.pop("rename_result", None)
                st.rerun()

    st.markdown("---")
    st.subheader("Drop Columns")

    drop_cols = st.multiselect("Select columns to drop", df.columns)
    if "prev_drop_cols" not in st.session_state:
        st.session_state["prev_drop_cols"] = drop_cols

    if drop_cols != st.session_state["prev_drop_cols"]:
        st.session_state.pop("drop_result", None)  
        st.session_state["prev_drop_cols"] = drop_cols

    if st.button("Drop Selected Columns"):
        st.session_state["history"].append(df.copy())

        if not drop_cols:
            st.warning("Select at least one column.")
            st.session_state.pop("drop_result", None)  

        else:
            df_copy = df.copy()

            before_cols = df_copy.columns.tolist()

            df_copy = df_copy.drop(columns=drop_cols)

            after_cols = df_copy.columns.tolist()

            removed = len(before_cols) - len(after_cols)

            if removed == 0:
                st.info("No columns were removed.")
            else:
                st.success(f"{removed} column(s) removed.")

            # ✅ SAVE DATA
            st.session_state["df"] = df_copy

            # 🔥 SAVE RESULT (THIS IS WHAT YOU WERE MISSING)
            st.session_state["drop_result"] = {
                "removed": drop_cols,
                "before": before_cols,
                "after": after_cols
            }

            add_log(
                operation="Drop Columns",
                columns=", ".join(drop_cols),
                method="Manual",
                action="Columns removed",
                affected=removed,
                details=f"{len(before_cols)} → {len(after_cols)}"
            )
    if "drop_result" in st.session_state:

        r = st.session_state["drop_result"]

        st.markdown("### 🔍 Result")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Before**")
            before_df = pd.DataFrame(r["before"], columns=["Columns Before"])

            # highlight removed columns
            def highlight_removed(val):
                if val in r["removed"]:
                    return "background-color: #ffcccc; color: red; font-weight: bold;"
                return ""

            st.dataframe(
                before_df.style.applymap(highlight_removed),
                use_container_width=True
            )

        with col2:
            st.markdown("**After**")
            st.dataframe(pd.DataFrame(r["after"], columns=["Columns After"]))

        st.caption(f"🔴 Removed column(s): {', '.join(r['removed'])}")

        if st.button("Clear result"):
            st.session_state["history"].append(df.copy())
            st.session_state.pop("drop_result", None)
            st.rerun()
    


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
            st.session_state["history"].append(df.copy())
            if not new_col_name.strip():
                st.warning("Enter column name.")
                return

            elif new_col_name in df.columns:
                st.warning("Column already exists.")
                return
            else:
                df_copy = df.copy()

                try:
                    if formula_type == "Division":
                        if (df_copy[col2] == 0).any():
                            st.warning("Division by zero detected → replaced with NaN")

                        df_copy[new_col_name] = df_copy[col1] / df_copy[col2].replace(0, np.nan)
                    # Apply formula
                    if formula_type == "Addition":
                        df_copy[new_col_name] = df_copy[col1] + df_copy[col2]

                    elif formula_type == "Subtraction":
                        df_copy[new_col_name] = df_copy[col1] - df_copy[col2]

                    elif formula_type == "Log":
                        if (df_copy[col1] <= 0).any():
                            st.warning("Log applied to non-positive values → adjusted")
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
                        df_copy[[col1] + ([col2] if col2 else []) + [new_col_name]].head(10),
                        use_container_width=True
                    )
                    st.caption("ℹ️ Result depends on previous transformations. Some operations may cancel each other out.")
                    if col2 is not None:
                        if abs(df_copy[col1].mean()) < abs(df_copy[col2].mean()) * 0.01:
                            st.caption("⚠️ Large scale difference between columns may dominate the result")

                    st.session_state["newcol_result"] = {
                        "col1": col1,
                        "col2": col2,
                        "new_col": new_col_name,
                        "preview": df_copy.head(5)
                    }
                except:
                    st.error("Error")
            
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

    handle_missing = st.selectbox(
        "Handle missing values",
        ["Keep as 'Missing'", "Drop rows"]
    )

    handle_outliers = st.selectbox(
        "Handle outliers",
        ["Keep", "Cap (IQR)", "Remove"]
    )

    if st.button("Apply Binning"):
        st.session_state["history"].append(df.copy())

        if not new_bin_col.strip():
            st.warning("Enter a name for new column.")

        elif new_bin_col in df.columns:
            st.warning("Column already exists.")

        else:
            df_copy = df.copy()
            series = df_copy[bin_col]

            # ---------------- HANDLE MISSING ----------------
            if handle_missing == "Drop rows":
                df_copy = df_copy.dropna(subset=[bin_col])
                series = df_copy[bin_col]

            # ---------------- HANDLE OUTLIERS ----------------
            if handle_outliers in ["Cap (IQR)", "Remove"]:
                Q1 = series.quantile(0.25)
                Q3 = series.quantile(0.75)
                IQR = Q3 - Q1

                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR

                if handle_outliers == "Remove":
                    df_copy = df_copy[(series >= lower) & (series <= upper)]
                    series = df_copy[bin_col]

                elif handle_outliers == "Cap (IQR)":
                    df_copy[bin_col] = series.clip(lower, upper)
                    series = df_copy[bin_col]

            # ---------------- BINNING ----------------
            if series.nunique() < bins:
                st.warning("Not enough unique values for this number of bins.")

            else:
                if bin_method == "Equal Width":
                    binned = pd.cut(series, bins=bins)
                else:
                    binned = pd.qcut(series, q=bins, duplicates="drop")

                df_copy[new_bin_col] = pd.Series(index=df_copy.index, dtype="object")
                df_copy.loc[series.index, new_bin_col] = binned.astype(str)

                if handle_missing == "Keep as 'Missing'":
                    df_copy[new_bin_col] = df_copy[new_bin_col].fillna("Missing")

                # ---------------- SAVE ----------------
                st.session_state["df"] = df_copy

                # ---------------- UI ----------------
                st.success(f"Binning applied on '{bin_col}'")

                st.caption(f"""
    Missing: {handle_missing}  
    Outliers: {handle_outliers}
    """)

                st.markdown("### Distribution")
                st.dataframe(
                    df_copy[new_bin_col].value_counts().to_frame("Count"),
                    use_container_width=True
                )

                # ---------------- PREVIEW ----------------
                st.markdown("### 🔍 Preview")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Before**")
                    st.dataframe(
                        df[[bin_col]].head(10),
                        use_container_width=True
                    )

                with col2:
                    st.markdown("**After**")
                    st.dataframe(
                        df_copy[[bin_col, new_bin_col]].head(10),
                        use_container_width=True
                    )

                # ---------------- WARNINGS ----------------
                if df_copy[new_bin_col].isna().sum() > 0:
                    st.caption("⚠️ Some values could not be binned due to missing data")

                # ---------------- LOG ----------------
                add_log(
                    operation="Binning",
                    columns=bin_col,
                    method=bin_method,
                    action="Discretized",
                    affected=len(df_copy),
                    details=f"{bins} bins → {new_bin_col}"
                )

    st.markdown("---")
