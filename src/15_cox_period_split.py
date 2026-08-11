"""
15_cox_period_split.py
The proportional-hazards test flagged age, Stage IV, and Triple Negative:
their effect changes over time. Here we estimate hazard ratios separately
for years 0-5 and years 5+ to SHOW how the effects shift.
Run from the project root:  python3 src/15_cox_period_split.py
"""
from pathlib import Path
import pandas as pd
from lifelines import CoxPHFitter

df = pd.read_csv(Path("data/processed/patients_analysis.csv"))
df = df[(df["stage_group"] != "Unknown") &
        (df["molecular_subtype"] != "Unknown")].copy()
df = df.dropna(subset=["age_at_diagnosis", "os_years", "os_event"])
df["age_per10yr"] = df["age_at_diagnosis"] / 10

stage_d = pd.get_dummies(df["stage_group"], prefix="stage").astype(int)
sub_d = pd.get_dummies(df["molecular_subtype"], prefix="subtype").astype(int)
base = pd.concat([
    df[["os_years", "os_event", "age_per10yr"]].reset_index(drop=True),
    stage_d.drop(columns=["stage_I"]).reset_index(drop=True),
    sub_d.drop(columns=["subtype_HR+/HER2-"]).reset_index(drop=True),
], axis=1)

def fit_and_show(data, label):
    cph = CoxPHFitter().fit(data, duration_col="os_years", event_col="os_event")
    print(f"\n{label}  (patients={len(data)}, deaths={int(data['os_event'].sum())})")
    print(cph.summary["exp(coef)"].round(2).rename("HR").to_string())

LM = 5  # landmark at 5 years

# Early: cap everyone's follow-up at 5 years (deaths after 5y count as survived-to-5).
early = base.copy()
beyond = early["os_years"] > LM
early.loc[beyond, "os_event"] = 0
early.loc[beyond, "os_years"] = LM
fit_and_show(early, f"YEARS 0-{LM} (early)")

# Late: only patients still alive past 5 years, with the clock reset to 0.
late = base[base["os_years"] > LM].copy()
late["os_years"] = late["os_years"] - LM
fit_and_show(late, f"YEARS {LM}+ (late, conditional on surviving {LM}y)")
