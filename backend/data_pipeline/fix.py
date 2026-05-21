import pandas as pd

df = pd.read_csv("cleaned/master_cutoffs.csv")

df = df.drop_duplicates(
    subset=["college_code", "branch_code", "category", "quota", "year", "cap_round"]
)

df["college_code"] = df["college_code"].astype(str).str.replace(".0", "", regex=False)
df["branch_code"] = df["branch_code"].astype(str).str.replace(".0", "", regex=False)

df["closing_rank"] = df["closing_rank"].apply(
    lambda x: "" if pd.isna(x) else int(float(x))
)

df["year"] = df["year"].astype(int)
df["cap_round"] = df["cap_round"].astype(int)

df.to_csv("cleaned/master_cutoffs_final.csv", index=False)

print(f"Rows: {len(df)}")
print("Saved to master_cutoffs_final.csv")