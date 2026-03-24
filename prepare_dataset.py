import pandas as pd
import numpy as np

# df2 = pd.read_csv("sample_data/Airports2.csv")

# # reduce size (dataset is huge)
# df2_small = df2.sample(10000, random_state=42)

# # save
# df2_small.to_csv("sample_data/flights_dataset.csv", index=False)


# print("Datasets prepared successfully.")

# ---------- LOAD ----------
df = pd.read_csv("sample_data/healthcare_dataset_main2.csv")

# ---------- ADD OUTLIERS ----------
# choose numeric columns
num_cols = df.select_dtypes(include=["int64", "float64"]).columns

for col in num_cols:
    if df[col].nunique() > 5:  # avoid categorical-like numbers
        # inject 2 extreme values per column
        df.loc[0, col] = df[col].max() * 20
        df.loc[1, col] = df[col].min() * 20
        df.loc[2, col] = df[col].min() * 20
        df.loc[3, col] = df[col].min() * 20
        df.loc[4, col] = df[col].min() * 20
        df.loc[5, col] = df[col].min() * 20

# ---------- SAVE ----------
df.to_csv("Healthcare_dataset_main2.csv", index=False)

print("Dataset with outliers created.")