"""
14_cox_model.py
Multivariable Cox proportional-hazards model: age + stage + subtype together.
Outputs hazard ratios (HR) with confidence intervals, and a forest plot.
Run from the project root:  python3 src/14_cox_model.py
"""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from lifelines import CoxPHFitter

df = pd.read_csv(Path("data/processed/patients_analysis.csv"))

df = df[(df["stage_group"] != "Unknown") &
        (df["molecular_subtype"] != "Unknown")].copy()
df = df.dropna(subset=["age_at_diagnosis", "os_years", "os_event"])

df["age_per10yr"] = df["age_at_diagnosis"] / 10

stage_d = pd.get_dummies(df["stage_group"], prefix="stage").astype(int)
sub_d = pd.get_dummies(df["molecular_subtype"], prefix="subtype").astype(int)

model_df = pd.concat([
    df[["os_years", "os_event", "age_per10yr"]].reset_index(drop=True),
    stage_d.drop(columns=["stage_I"]).reset_index(drop=True),           # ref = Stage I
    sub_d.drop(columns=["subtype_HR+/HER2-"]).reset_index(drop=True),   # ref = HR+/HER2-
], axis=1)

cph = CoxPHFitter()
cph.fit(model_df, duration_col="os_years", event_col="os_event")

# Clean hazard-ratio table.
s = cph.summary[["exp(coef)", "exp(coef) lower 95%", "exp(coef) upper 95%", "p"]].copy()
s.columns = ["HR", "CI_low", "CI_high", "p"]
print("model on", len(model_df), "patients,", int(model_df["os_event"].sum()), "deaths\n")
print(s.round(3).to_string())
print("\nConcordance index (0.5 = chance, 1.0 = perfect):",
      round(cph.concordance_index_, 3))

plt.figure(figsize=(8, 5))
cph.plot(hazard_ratios=True)
plt.axvline(1.0, color="grey", linestyle="--", linewidth=1)  # HR = 1 => no effect
plt.title("Cox model - hazard ratios (95% CI)")
plt.savefig(Path("reports/figures/cox_forest.png"), dpi=120, bbox_inches="tight")
print("saved -> reports/figures/cox_forest.png")

# --- Check the proportional-hazards assumption (Schoenfeld residuals) ---
from lifelines.statistics import proportional_hazard_test
print("\n--- Proportional-hazards assumption check ---")
ph = proportional_hazard_test(cph, model_df, time_transform="rank")
print(ph.summary[["test_statistic", "p"]].round(3).to_string())
print("(small p, e.g. < 0.05, = that variable's effect changes over time)")
