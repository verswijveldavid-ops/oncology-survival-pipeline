"""
08_sdtm_dm.py
Map the raw patient data into the CDISC SDTM DM (Demographics) domain.
DM = one standardized row per subject.
Run from the project root:  python3 src/08_sdtm_dm.py
"""
from pathlib import Path
import pandas as pd

src = pd.read_csv(Path("data/processed/patients.csv"))

# Build DM by renaming/recoding raw fields into SDTM standard columns.
dm = pd.DataFrame({
    "STUDYID": "TCGA-BRCA",                 # fixed study label
    "DOMAIN": "DM",                          # fixed domain label
    "USUBJID": src["bcr_patient_barcode"],   # unique subject id
    "SUBJID": src["bcr_patient_barcode"].str.split("-").str[-1],  # short id
    "SEX": src["gender"].map({"FEMALE": "F", "MALE": "M"}),       # SDTM codes
    "AGE": src["age_at_diagnosis"],
    "AGEU": "YEARS",                         # unit for AGE
    "RACE": src["race"],
    "ETHNIC": src["ethnicity"],
})

out = Path("data/processed/sdtm_dm.csv")
dm.to_csv(out, index=False)

print("saved ->", out, "| shape:", dm.shape)
print("\nSEX counts:", dm["SEX"].value_counts().to_dict())
print("\nfirst rows:")
print(dm.head().to_string(index=False))
