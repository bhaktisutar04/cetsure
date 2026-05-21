import pandas as pd

df = pd.read_csv("cleaned/master_cutoffs.csv")
print("Before:", len(df))

df = df.drop_duplicates(
    subset=["college_code", "branch_code", "category", "quota", "year", "cap_round"]
)
print("After:", len(df))

df.to_csv("cleaned/master_cutoffs_dedup.csv", index=False)
print("Saved to master_cutoffs_dedup.csv")