"""
02_build_patient_table.py
Build one clean row per patient: demographics + RECONCILED survival + treatments.
Survival now comes from src/18 (all follow-up files combined), not the patient
file alone. Run 18 before this. Run from project root.
"""
from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")
MISSING = ["[Not Available]", "[Not Applicable]", "[Unknown]",
           "[Not Evaluated]", "[Discrepancy]", "[Completed]"]

def read_biotab(pattern):
    return pd.read_csv(next(RAW_DIR.rglob(pattern)), sep="\t", skiprows=[1, 2],
                       dtype=str, na_values=MISSING)

# Step 1: demographics backbone from the patient file.
keep = ["bcr_patient_barcode", "gender", "age_at_diagnosis", "race", "ethnicity",
        "ajcc_pathologic_tumor_stage",
        "er_status_by_ihc", "pr_status_by_ihc", "her2_status_by_ihc"]
patients = read_biotab("*clinical_patient_brca.txt")[keep]
patients["age_at_diagnosis"] = pd.to_numeric(patients["age_at_diagnosis"], errors="coerce")

# Step 2: survival from the RECONCILED follow-up (all files combined).
rec = pd.read_csv(Path("data/processed/followup_reconciled.csv")) \
        .rename(columns={"os_time_days": "os_time"})
patients = patients.merge(rec[["bcr_patient_barcode", "vital_status", "os_time", "os_event"]],
                          on="bcr_patient_barcode", how="left")

# Step 3: treatments.
drugs = read_biotab("*clinical_drug_brca.txt")
drugs["type_l"] = drugs["pharmaceutical_therapy_type"].str.lower()
drug_summary = drugs.groupby("bcr_patient_barcode").agg(
    n_drugs=("pharmaceutical_therapy_drug_name", "size"),
    got_chemo=("type_l", lambda s: s.str.contains("chemo", na=False).any()),
    got_hormone=("type_l", lambda s: s.str.contains("hormone", na=False).any()),
).reset_index()
patients = patients.merge(drug_summary, on="bcr_patient_barcode", how="left")
patients["n_drugs"] = patients["n_drugs"].fillna(0).astype(int)
patients["got_chemo"] = patients["got_chemo"].fillna(False)
patients["got_hormone"] = patients["got_hormone"].fillna(False)
radiation = read_biotab("*clinical_radiation_brca.txt")
patients["got_radiation"] = patients["bcr_patient_barcode"].isin(
    radiation["bcr_patient_barcode"].unique())

patients.to_csv(Path("data/processed/patients.csv"), index=False)
print("saved patients.csv:", patients.shape, "| deaths:", int(patients["os_event"].sum()))
