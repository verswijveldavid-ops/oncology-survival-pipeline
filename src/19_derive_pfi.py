"""
19_derive_pfi.py
Second endpoint: progression-free survival (PFS). Event = cancer recurrence
OR death, whichever comes first. Recurrence dates come from the new-tumor-event
file. Adds pfi_years/pfi_event to the analysis table and plots PFS by stage.
Run from the project root:  python3 src/19_derive_pfi.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from lifelines import KaplanMeierFitter
from lifelines.statistics import multivariate_logrank_test
from lifelines.plotting import add_at_risk_counts

RAW_DIR = Path("data/raw")
MISSING = ["[Not Available]", "[Not Applicable]", "[Unknown]",
           "[Not Evaluated]", "[Discrepancy]", "[Completed]"]

df = pd.read_csv(Path("data/processed/patients_analysis.csv"))
# Drop leftovers so re-running is safe (the lesson from script 13).
df = df.drop(columns=[c for c in ["rec_day", "pfi_event", "pfi_years"] if c in df.columns])

# Earliest recurrence day per patient, from the new-tumor-event file.
nte = pd.read_csv(next(RAW_DIR.rglob("*clinical_nte_brca.txt")),
                  sep="\t", skiprows=[1, 2], dtype=str, na_values=MISSING)
nte["rec_day"] = pd.to_numeric(nte["new_tumor_event_dx_days_to"], errors="coerce")
rec = nte.groupby("bcr_patient_barcode")["rec_day"].min().reset_index()
df = df.merge(rec, on="bcr_patient_barcode", how="left")

# PFS: event if recurrence OR death; time = earliest of the two (else last contact).
has_recur = df["rec_day"].notna() & (df["rec_day"] > 0)
df["pfi_event"] = (has_recur | (df["os_event"] == 1)).astype(int)
rec_years = df["rec_day"] / 365.25
df["pfi_years"] = df["os_years"]
df.loc[has_recur, "pfi_years"] = np.minimum(df.loc[has_recur, "os_years"], rec_years[has_recur])
df = df[df["pfi_years"] > 0]

df.to_csv(Path("data/processed/patients_analysis.csv"), index=False)
print("PFS events (recurrence or death):", int(df["pfi_event"].sum()), "of", len(df))
print("OS events (death only):        ", int(df["os_event"].sum()))

# PFS curve by stage.
d = df[df["stage_group"].isin(["I", "II", "III", "IV"])]
plt.figure(figsize=(9, 6)); ax = plt.subplot(111); fitters = []
for s in ["I", "II", "III", "IV"]:
    g = d[d["stage_group"] == s]; k = KaplanMeierFitter()
    k.fit(g["pfi_years"], g["pfi_event"], label=f"Stage {s} (n={len(g)})")
    k.plot_survival_function(ax=ax, ci_show=False); fitters.append(k)
add_at_risk_counts(*fitters, ax=ax)
ax.set_title("Progression-Free Survival by Stage - TCGA-BRCA")
ax.set_xlabel("Years from diagnosis"); ax.set_ylabel("Progression-free probability")
ax.set_ylim(0, 1); plt.tight_layout()
plt.savefig(Path("reports/figures/pfi_by_stage.png"), dpi=120)
p = multivariate_logrank_test(d["pfi_years"], d["stage_group"], d["pfi_event"]).p_value
print("saved -> reports/figures/pfi_by_stage.png | log-rank p:", p)
