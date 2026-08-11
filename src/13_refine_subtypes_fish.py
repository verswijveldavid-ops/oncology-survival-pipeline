"""
13_refine_subtypes_fish.py
Refine HER2 status (and molecular subtype) using FISH to resolve the
equivocal/missing IHC cases -- the real clinical tie-breaker rule.
Safe to run repeatedly (idempotent).
Run from the project root:  python3 src/13_refine_subtypes_fish.py
"""
from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")
MISSING = ["[Not Available]", "[Not Applicable]", "[Unknown]",
           "[Not Evaluated]", "[Discrepancy]", "[Completed]"]

df = pd.read_csv(Path("data/processed/patients_analysis.csv"))

# Drop any leftovers from a previous run so re-running is always safe.
df = df.drop(columns=[c for c in ["her2_fish_status", "her2_effective"]
                      if c in df.columns])

# Bring HER2 FISH result in from the raw patient file, matched by barcode.
raw = pd.read_csv(next(RAW_DIR.rglob("*clinical_patient_brca.txt")),
                  sep="\t", skiprows=[1, 2], dtype=str, na_values=MISSING)
df = df.merge(raw[["bcr_patient_barcode", "her2_fish_status"]],
              on="bcr_patient_barcode", how="left")

def effective_her2(row):
    ihc = row["her2_status_by_ihc"]
    fish = row["her2_fish_status"]
    if ihc == "Positive":
        return "Positive"
    if ihc == "Negative":
        return "Negative"
    if fish == "Positive":     # FISH resolves an equivocal/missing IHC
        return "Positive"
    if fish == "Negative":
        return "Negative"
    return "Unknown"

df["her2_effective"] = df.apply(effective_her2, axis=1)

def subtype(row):
    er, pr, her2 = row["er_status_by_ihc"], row["pr_status_by_ihc"], row["her2_effective"]
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

print("subtype counts (FISH-refined):")
print(df["molecular_subtype"].value_counts().to_string())
