"""
05_survival_km.py
Stop 6, step 1: overall Kaplan-Meier survival curve for the whole cohort.
Run from the project root:  python3 src/05_survival_km.py
"""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # draw to a file, no pop-up window needed
import matplotlib.pyplot as plt
from lifelines import KaplanMeierFitter

df = pd.read_csv(Path("data/processed/patients_analysis.csv"))

# Fit the Kaplan-Meier estimator: how long (os_years) and did they die (os_event).
kmf = KaplanMeierFitter()
kmf.fit(durations=df["os_years"], event_observed=df["os_event"], label="All patients")

# Draw the curve.
ax = kmf.plot_survival_function()
ax.set_title(f"Overall Survival — TCGA-BRCA (n={len(df)})")
ax.set_xlabel("Years from diagnosis")
ax.set_ylabel("Survival probability")
ax.set_ylim(0, 1)
plt.tight_layout()

out = Path("reports/figures/km_overall.png")
plt.savefig(out, dpi=120)

print("saved plot ->", out)
median = kmf.median_survival_time_
print("median survival (years):", median, "(inf = never reached 50%)")
