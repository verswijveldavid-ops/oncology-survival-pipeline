"""
10_sdtm_ds.py
Map subject outcome into the CDISC SDTM DS (Disposition) domain.
DS = what happened to the subject. One row per subject here.
Run from the project root:  python3 src/10_sdtm_ds.py
"""
from pathlib import Path
import pandas as pd

df = pd.read_csv(Path("data/processed/patients.csv"))

ds = pd.DataFrame({
    "STUDYID": "TCGA-BRCA",
    "DOMAIN": "DS",
    "USUBJID": df["bcr_patient_barcode"],
    "DSSEQ": 1,  # one disposition record per subject
    "DSDECOD": df["vital_status"].map({"Dead": "DEATH", "Alive": "ALIVE"}),
    "DSTERM": df["vital_status"].map({"Dead": "DEATH",
                                      "Alive": "ALIVE AT LAST CONTACT"}),
})

# DSSTDY: study day of the event -> death day if dead, else last contact day.
ds["DSSTDY"] = df["last_contact_days_to"]
dead = df["vital_status"] == "Dead"
ds.loc[dead, "DSSTDY"] = df.loc[dead, "death_days_to"]

out = Path("data/processed/sdtm_ds.csv")
ds.to_csv(out, index=False)

print("saved ->", out, "| shape:", ds.shape)
print("\nDSDECOD counts:", ds["DSDECOD"].value_counts().to_dict())
print("\nexamples:")
print(ds[ds["USUBJID"].isin(["TCGA-A1-A0SK", "TCGA-3C-AAAU"])].to_string(index=False))
