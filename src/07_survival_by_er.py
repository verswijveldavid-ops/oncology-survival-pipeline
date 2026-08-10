"""
07_survival_by_er.py
Survival by ER (estrogen receptor) status: Positive vs Negative.
Run from the project root:  python3 src/07_survival_by_er.py
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
df = df[df["er_status_by_ihc"].isin(["Positive", "Negative"])]

plt.figure(figsize=(9, 6))
ax = plt.subplot(111)

fitters = []
for status in ["Positive", "Negative"]:
    group = df[df["er_status_by_ihc"] == status]
    k = KaplanMeierFitter()
    k.fit(group["os_years"], group["os_event"], label=f"ER {status}")
    k.plot_survival_function(ax=ax, ci_show=False)
    fitters.append(k)

add_at_risk_counts(*fitters, ax=ax)
ax.set_title("Overall Survival by ER Status — TCGA-BRCA")
ax.set_xlabel("Years from diagnosis")
ax.set_ylabel("Survival probability")
ax.set_ylim(0, 1)
plt.tight_layout()

out = Path("reports/figures/km_by_er.png")
plt.savefig(out, dpi=120)

result = multivariate_logrank_test(df["os_years"], df["er_status_by_ihc"], df["os_event"])
print("saved plot ->", out)
print("group sizes:\n", df["er_status_by_ihc"].value_counts().to_string())
print("log-rank p-value:", result.p_value)
