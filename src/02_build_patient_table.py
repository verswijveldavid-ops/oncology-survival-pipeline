"""
02_build_patient_table.py
Stop 3, steps 1-3: patient backbone -> survival columns -> glue on treatments.
Run from the project root:  python3 src/02_build_patient_table.py
"""
from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")

MISSING = ["[Not Available]", "[Not Applicable]", "[Unknown]",
           "[Not Evaluated]", "[Discrepancy]", "[Completed]"]


def read_biotab(pattern: str) -> pd.DataFrame:
    """Find a raw file by name pattern and read it (skipping junk rows 2-3)."""
    path = next(RAW_DIR.rglob(pattern))
    return pd.read_csv(path, sep="\t", skiprows=[1, 2], dtype=str, na_values=MISSING)


# --- Step 1: backbone ---------------------------------------------------
patients = read_biotab("*clinical_patient_brca.txt")
keep = [
    "bcr_patient_barcode",
    "gender", "age_at_diagnosis", "race", "ethnicity",
    "ajcc_pathologic_tumor_stage",
    "er_status_by_ihc", "pr_status_by_ihc", "her2_status_by_ihc",
    "vital_status", "death_days_to", "last_contact_days_to",
]
patients = patients[keep]

# --- Step 2: survival columns ------------------------------------------
for col in ["age_at_diagnosis", "death_days_to", "last_contact_days_to"]:
    patients[col] = pd.to_numeric(patients[col], errors="coerce")

patients["os_event"] = (patients["vital_status"] == "Dead").astype(int)
patients["os_time"] = patients["last_contact_days_to"]
dead = patients["vital_status"] == "Dead"
patients.loc[dead, "os_time"] = patients.loc[dead, "death_days_to"]

# --- Step 3: squeeze treatment files, then glue on ---------------------

# DRUGS: many rows per patient -> one summary row per patient.
drugs = read_biotab("*clinical_drug_brca.txt")
drugs["type_l"] = drugs["pharmaceutical_therapy_type"].str.lower()
drug_summary = drugs.groupby("bcr_patient_barcode").agg(
    n_drugs=("pharmaceutical_therapy_drug_name", "size"),
    got_chemo=("type_l", lambda s: s.str.contains("chemo", na=False).any()),
    got_hormone=("type_l", lambda s: s.str.contains("hormone", na=False).any()),
).reset_index()

# Glue the drug summary onto the backbone (keep all patients).
patients = patients.merge(drug_summary, on="bcr_patient_barcode", how="left")

# Patients with no drug rows -> fill sensible blanks.
patients["n_drugs"] = patients["n_drugs"].fillna(0).astype(int)
patients["got_chemo"] = patients["got_chemo"].fillna(False)
patients["got_hormone"] = patients["got_hormone"].fillna(False)

# RADIATION: simpler -> did this patient appear in the radiation file at all?
radiation = read_biotab("*clinical_radiation_brca.txt")
rad_patients = radiation["bcr_patient_barcode"].unique()
patients["got_radiation"] = patients["bcr_patient_barcode"].isin(rad_patients)

# --- Checks -------------------------------------------------------------
print("shape:", patients.shape)
print("\ngot chemo:    ", int(patients["got_chemo"].sum()))
print("got hormone:  ", int(patients["got_hormone"].sum()))
print("got radiation:", int(patients["got_radiation"].sum()))
print("\nsample (our 6-drug patient included):")
cols = ["bcr_patient_barcode", "os_time", "os_event",
        "n_drugs", "got_chemo", "got_hormone", "got_radiation"]
print(patients[patients["bcr_patient_barcode"] == "TCGA-A2-A04V"][cols].to_string(index=False))
print(patients[cols].head(8).to_string(index=False))

# --- Step 4: save the finished table to disk ---------------------------
OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)
patients.to_csv(OUT_DIR / "patients.csv", index=False)
print("\nsaved ->", OUT_DIR / "patients.csv", "| shape:", patients.shape)
