"""
04_build_analysis_table.py
Stop 5: apply documented data-quality decisions -> analysis-ready table.
Decisions:
  - drop patients with follow-up time <= 0 (no usable survival info)
  - collapse cancer stage into clean groups (I, II, III, IV, Unknown)
Run from the project root:  python3 src/04_build_analysis_table.py
"""
from pathlib import Path
import pandas as pd

df = pd.read_csv(Path("data/processed/patients.csv"))
before = len(df)

# 1. Drop invalid follow-up time. Documented, defensible, reversible (raw kept).
df = df[df["os_time"] > 0].copy()
after = len(df)

# 2. Collapse AJCC stage (IA, IIB, IIIC...) into main groups.
def stage_group(s):
    if pd.isna(s) or s == "Stage X":
        return "Unknown"
    s = s.replace("Stage ", "")
    if s.startswith("IV"):
        return "IV"
    if s.startswith("III"):
        return "III"
    if s.startswith("II"):
        return "II"
    if s.startswith("I"):
        return "I"
    return "Unknown"

df["stage_group"] = df["ajcc_pathologic_tumor_stage"].apply(stage_group)

# 3. Follow-up time in years, easier to read than days.
df["os_years"] = (df["os_time"] / 365.25).round(2)

df.to_csv(Path("data/processed/patients_analysis.csv"), index=False)

print(f"rows: {before} -> {after}  (dropped {before - after} with follow-up time <= 0)")
print("\nstage groups:")
print(df["stage_group"].value_counts().to_string())
print("\nevents (1 = died):", int(df["os_event"].sum()), "of", after)
