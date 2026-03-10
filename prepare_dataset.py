import pandas as pd
import numpy as np

df2 = pd.read_csv("sample_data/Airports2.csv")

# reduce size (dataset is huge)
df2_small = df2.sample(10000, random_state=42)

# save
df2_small.to_csv("sample_data/flights_dataset.csv", index=False)


print("Datasets prepared successfully.")