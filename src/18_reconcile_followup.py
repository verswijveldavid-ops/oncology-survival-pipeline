"""
18_reconcile_followup.py
Combine the patient file with all three follow-up form versions to get each
patient's LATEST known status. Fixes truncated follow-up in the first table.
Writes data/processed/followup_reconciled.csv and reports the impact.
Run from the project root:  python3 src/18_reconcile_followup.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

RAW_DIR = Path("data/raw")
MISSING = ["[Not Available]", "[Not Applicable]", "[Unknown]",
           "[Not Evaluated]", "[Discrepancy]", "[Completed]"]
NEEDED = ["bcr_patient_barcode", "vital_status",
          "last_contact_days_to", "death_days_to"]

def read(path):
    df = pd.read_csv(path, sep="\t", skiprows=[1, 2], dtype=str, na_values=MISSING)
    for col in NEEDED:               # some follow-up versions lack a column
        if col not in df.columns:
            df[col] = np.nan
    return df[NEEDED]

# Stack the patient file and every follow-up file into one long list of records.
frames = [read(next(RAW_DIR.rglob("*clinical_patient_brca.txt")))]
frames += [read(p) for p in RAW_DIR.rglob("*clinical_follow_up_v*_brca.txt")]
allrows = pd.concat(frames, ignore_index=True)
for col in ["last_contact_days_to", "death_days_to"]:
    allrows[col] = pd.to_numeric(allrows[col], errors="coerce")

def reconcile(g):
    deaths = g["death_days_to"].dropna()
    contacts = g["last_contact_days_to"].dropna()
    is_dead = (g["vital_status"] == "Dead").any() or len(deaths) > 0
    if is_dead:
        t = deaths.max() if len(deaths) else (contacts.max() if len(contacts) else np.nan)
        return pd.Series({"vital_status": "Dead", "os_time_days": t, "os_event": 1})
    t = contacts.max() if len(contacts) else np.nan
    return pd.Series({"vital_status": "Alive", "os_time_days": t, "os_event": 0})

rec = allrows.groupby("bcr_patient_barcode").apply(reconcile).reset_index()
rec.to_csv(Path("data/processed/followup_reconciled.csv"), index=False)

# --- Impact vs the current (patient-file-only) table --------------------
cur = pd.read_csv(Path("data/processed/patients.csv"))[
    ["bcr_patient_barcode", "vital_status", "os_time", "os_event"]]
m = cur.merge(rec, on="bcr_patient_barcode", suffixes=("_old", "_new"))

print("deaths  old ->", int(cur["os_event"].sum()),
      "| new ->", int(rec["os_event"].sum()))
newly_dead = int(((m["os_event_old"] == 0) & (m["os_event_new"] == 1)).sum())
print("patients newly found dead in follow-up:", newly_dead)

alive = m[m["os_event_new"] == 0]
print("\nmedian follow-up (alive), years  old -> {:.1f} | new -> {:.1f}".format(
    (alive["os_time"] / 365.25).median(),
    (alive["os_time_days"] / 365.25).median()))
longer = int((m["os_time_days"] > m["os_time"] + 0.5).sum())
print("patients whose follow-up got longer:", longer)
