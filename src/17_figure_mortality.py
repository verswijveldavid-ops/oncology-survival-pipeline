"""
17_figure_mortality.py
A figure from Table 1: percentage of patients who died, by stage and by
molecular subtype. Answers "which groups do worse" at a glance.
Run from the project root:  python3 src/17_figure_mortality.py
"""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv(Path("data/processed/patients_analysis.csv"))
df["dead"] = (df["vital_status"] == "Dead").astype(int)

# Colours: one accessible hue (single measure), recessive greys for structure.
BAR, INK, MUTED, GRID = "#B44A3F", "#1a1a1a", "#6b6b6b", "#e6e6e6"

def draw(ax, col, order, title, xlabel):
    sub = df[df[col].isin(order)]
    rate = (sub.groupby(col)["dead"].mean() * 100).reindex(order)
    n = sub.groupby(col).size().reindex(order)
    x = range(len(order))
    ax.bar(x, rate.values, width=0.62, color=BAR, zorder=3)
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"{o}\n(n={int(ni)})" for o, ni in zip(order, n.values)],
                       fontsize=9, color=INK)
    ax.set_title(title, fontsize=12, color=INK, loc="left", pad=8)
    ax.set_ylim(0, 50)
    ax.set_ylabel("Patients who died (%)", fontsize=10, color=MUTED)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]:
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, length=0)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8, zorder=0)
    ax.set_xlabel(xlabel, fontsize=10, color=MUTED)
    for xi, v in zip(x, rate.values):
        ax.text(xi, v + 1.2, f"{v:.0f}%", ha="center", va="bottom",
                fontsize=11, fontweight="bold", color=INK)

fig, axes = plt.subplots(1, 2, figsize=(10, 4.6))
draw(axes[0], "stage_group", ["I", "II", "III", "IV"], "By stage", "Cancer stage")
draw(axes[1], "molecular_subtype",
     ["HR+/HER2-", "HER2-positive", "Triple Negative"], "By molecular subtype", "Subtype")

fig.suptitle("Who died? Mortality by group - TCGA-BRCA (n=1035, 103 deaths)",
             fontsize=13, color=INK, x=0.02, ha="left")
fig.text(0.02, -0.02,
         "Unknown-stage/subtype patients excluded. Treatment groups omitted (confounded).",
         fontsize=7.5, color=MUTED, ha="left")
plt.tight_layout()
plt.savefig(Path("reports/figures/table1_mortality.png"), dpi=150, bbox_inches="tight")
print("saved -> reports/figures/table1_mortality.png")
