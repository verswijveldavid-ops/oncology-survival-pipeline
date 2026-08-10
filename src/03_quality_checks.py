"""
03_quality_checks.py
Stop 4: run CDA-style edit checks on the clean patient table.
We flag, we don't fix. Every problem row is written to dq_issues.csv.
Run from the project root:  python3 src/03_quality_checks.py
"""
from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")
MISSING = ["[Not Available]", "[Not Applicable]", "[Unknown]",
           "[Not Evaluated]", "[Discrepancy]", "[Completed]"]

patients = pd.read_csv(Path("data/processed/patients.csv"))
issues = []

def flag(mask, category, check_name, detail_col):
    """Record every row matching `mask` as one issue."""
    for _, row in patients[mask].iterrows():
        issues.append({
            "bcr_patient_barcode": row["bcr_patient_barcode"],
            "category": category,
            "check": check_name,
            "detail": f"{detail_col}={row[detail_col]}",
        })

# 1. MISSING / REQUIRED
flag(patients["vital_status"].isna(), "missing", "missing_vital_status", "vital_status")
flag(patients["os_time"].isna(), "missing", "missing_follow_up_time", "os_time")

# 2. VALIDITY / RANGE
flag((patients["age_at_diagnosis"] < 18) | (patients["age_at_diagnosis"] > 100),
     "validity", "age_out_of_range", "age_at_diagnosis")
flag(patients["os_time"] < 0, "validity", "negative_follow_up_time", "os_time")
flag(patients["os_time"] == 0, "validity", "zero_follow_up_time", "os_time")

# 3. CONSISTENCY (cross-field)
dead = patients["vital_status"] == "Dead"
alive = patients["vital_status"] == "Alive"
flag(dead & patients["death_days_to"].isna(),
     "consistency", "dead_without_death_day", "vital_status")
flag(alive & patients["death_days_to"].notna(),
     "consistency", "alive_with_death_day", "death_days_to")
flag((patients["os_event"] == 1) != dead,
     "consistency", "event_flag_mismatch", "os_event")

# 4. TIMELINE / LOGIC
flag(dead & (patients["death_days_to"] <= 0),
     "timeline", "died_at_or_before_diagnosis", "death_days_to")

# 5. CONTROLLED TERMS
flag(~patients["gender"].isin(["FEMALE", "MALE"]) & patients["gender"].notna(),
     "controlled_term", "gender_not_allowed", "gender")
stage = patients["ajcc_pathologic_tumor_stage"]
flag(stage.isna() | stage.eq("Stage X"),
     "controlled_term", "stage_unknown_or_missing", "ajcc_pathologic_tumor_stage")

# 6. UNIQUENESS
flag(patients["bcr_patient_barcode"].duplicated(keep=False),
     "uniqueness", "duplicate_barcode", "bcr_patient_barcode")

# 7. REFERENTIAL (cross-file): a treatment record with no matching patient
patient_ids = set(patients["bcr_patient_barcode"])
for name, pattern in [("drug", "*clinical_drug_brca.txt"),
                      ("radiation", "*clinical_radiation_brca.txt")]:
    raw = pd.read_csv(next(RAW_DIR.rglob(pattern)), sep="\t", skiprows=[1, 2],
                      dtype=str, na_values=MISSING)
    for orphan in sorted(set(raw["bcr_patient_barcode"]) - patient_ids):
        issues.append({"bcr_patient_barcode": orphan, "category": "referential",
                       "check": f"orphan_{name}_record",
                       "detail": f"in {name} file, not in patient file"})

# --- save + summarize ---------------------------------------------------
issues_df = pd.DataFrame(issues,
    columns=["bcr_patient_barcode", "category", "check", "detail"])
issues_df.to_csv(Path("data/processed/dq_issues.csv"), index=False)

print("total issues:", len(issues_df))
print("\nby category:")
print(issues_df["category"].value_counts().to_string())
print("\nby check:")
print(issues_df["check"].value_counts().to_string())
