"""
11_derive_subtypes.py
Derive breast-cancer molecular subtype from ER, PR, HER2 (IHC surrogate),
and add it to the analysis table.
Run from the project root:  python3 src/11_derive_subtypes.py
"""
from pathlib import Path
import pandas as pd

df = pd.read_csv(Path("data/processed/patients_analysis.csv"))

def subtype(row):
    er = row["er_status_by_ihc"]
    pr = row["pr_status_by_ihc"]
    her2 = row["her2_status_by_ihc"]
    hr_positive = (er == "Positive") or (pr == "Positive")
    if her2 == "Positive":
        return "HER2-positive"
    if her2 == "Negative" and hr_positive:
        return "HR+/HER2-"
    if her2 == "Negative" and er == "Negative" and pr == "Negative":
        return "Triple Negative"
    return "Unknown"

df["molecular_subtype"] = df.apply(subtype, axis=1)

df.to_csv(Path("data/processed/patients_analysis.csv"), index=False)

print("subtype counts:")
print(df["molecular_subtype"].value_counts().to_string())
print("\ntotal:", len(df))
