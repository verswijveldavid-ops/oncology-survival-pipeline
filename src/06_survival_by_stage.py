"""
06_survival_by_stage.py
Stop 6, step 2: Kaplan-Meier survival by cancer stage, with a log-rank
test and a "numbers at risk" table. The table shows how many patients
remain at each time -> where it gets small, the curve is not trustworthy.
Run from the project root:  python3 src/06_survival_by_stage.py
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
df = df[df["stage_group"] != "Unknown"]

plt.figure(figsize=(9, 6))
ax = plt.subplot(111)

fitters = []
for stage in ["I", "II", "III", "IV"]:
    group = df[df["stage_group"] == stage]
    k = KaplanMeierFitter()
    k.fit(group["os_years"], group["os_event"], label=f"Stage {stage}")
    k.plot_survival_function(ax=ax, ci_show=False)
    fitters.append(k)

# Numbers-at-risk table under the plot. Full timeline kept on purpose,
# so the reader can see the data thin out instead of hiding it.
add_at_risk_counts(*fitters, ax=ax)

ax.set_title("Overall Survival by Stage — TCGA-BRCA")
ax.set_xlabel("Years from diagnosis")
ax.set_ylabel("Survival probability")
ax.set_ylim(0, 1)
plt.tight_layout()

out = Path("reports/figures/km_by_stage.png")
plt.savefig(out, dpi=120)

result = multivariate_logrank_test(df["os_years"], df["stage_group"], df["os_event"])
print("saved plot ->", out)
print("log-rank p-value:", result.p_value)
