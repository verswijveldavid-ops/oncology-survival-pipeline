"""
12_survival_by_subtype.py
Kaplan-Meier survival by molecular subtype (HR+/HER2-, HER2-positive,
Triple Negative), with log-rank test and numbers-at-risk table.
Run from the project root:  python3 src/12_survival_by_subtype.py
"""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from lifelines import KaplanMeierFitter
from lifelines.statistics import multivariate_logrank_test
from lifelines.plotting import add_at_risk_counts

df = pd.read_csv(Path("data/processed/patients_analysis.csv"))
subtypes = ["HR+/HER2-", "HER2-positive", "Triple Negative"]
df = df[df["molecular_subtype"].isin(subtypes)]

plt.figure(figsize=(9, 6))
ax = plt.subplot(111)

fitters = []
for st in subtypes:
    group = df[df["molecular_subtype"] == st]
    k = KaplanMeierFitter()
    k.fit(group["os_years"], group["os_event"], label=f"{st} (n={len(group)})")
    k.plot_survival_function(ax=ax, ci_show=False)
    fitters.append(k)

add_at_risk_counts(*fitters, ax=ax)
ax.set_title("Overall Survival by Molecular Subtype - TCGA-BRCA")
ax.set_xlabel("Years from diagnosis")
ax.set_ylabel("Survival probability")
ax.set_ylim(0, 1)
plt.tight_layout()

out = Path("reports/figures/km_by_subtype.png")
plt.savefig(out, dpi=120)

result = multivariate_logrank_test(df["os_years"], df["molecular_subtype"], df["os_event"])
print("saved plot ->", out)
print("log-rank p-value:", result.p_value)
