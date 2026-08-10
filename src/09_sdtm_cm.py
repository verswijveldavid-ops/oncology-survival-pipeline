"""
09_sdtm_cm.py
Map the raw drug file into the CDISC SDTM CM (Concomitant Medications) domain.
CM = one row per drug (many per subject), numbered with CMSEQ.
Run from the project root:  python3 src/09_sdtm_cm.py
"""
from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")
MISSING = ["[Not Available]", "[Not Applicable]", "[Unknown]",
           "[Not Evaluated]", "[Discrepancy]", "[Completed]"]

drugs = pd.read_csv(next(RAW_DIR.rglob("*clinical_drug_brca.txt")),
                    sep="\t", skiprows=[1, 2], dtype=str, na_values=MISSING)

cm = pd.DataFrame({
    "STUDYID": "TCGA-BRCA",
    "DOMAIN": "CM",
    "USUBJID": drugs["bcr_patient_barcode"],
    "CMTRT": drugs["pharmaceutical_therapy_drug_name"].str.upper(),  # reported name
    "CMCLAS": drugs["pharmaceutical_therapy_type"],                  # drug class
    "CMSTDY": pd.to_numeric(drugs["pharmaceutical_tx_started_days_to"], errors="coerce"),
    "CMENDY": pd.to_numeric(drugs["pharmaceutical_tx_ended_days_to"], errors="coerce"),
})

# CMSEQ: number the drugs 1..n within each subject, ordered by start day.
cm = cm.sort_values(["USUBJID", "CMSTDY"]).reset_index(drop=True)
cm["CMSEQ"] = cm.groupby("USUBJID").cumcount() + 1

# Standard column order.
cm = cm[["STUDYID", "DOMAIN", "USUBJID", "CMSEQ",
         "CMTRT", "CMCLAS", "CMSTDY", "CMENDY"]]

out = Path("data/processed/sdtm_cm.csv")
cm.to_csv(out, index=False)

print("saved ->", out, "| shape:", cm.shape)
print("\nour 6-drug patient in CM form:")
print(cm[cm["USUBJID"] == "TCGA-A2-A04V"].to_string(index=False))
