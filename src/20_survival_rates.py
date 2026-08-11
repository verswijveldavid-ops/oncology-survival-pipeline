"""
20_survival_rates.py
Plain-language survival numbers: out of 100 patients in a group, how many
are still alive at 5 and 10 years. Saved for the dashboard headline.
Run from the project root:  python3 src/20_survival_rates.py
"""
from pathlib import Path
import pandas as pd
from lifelines import KaplanMeierFitter

df = pd.read_csv(Path("data/processed/patients_analysis.csv"))

def alive_pct(years, mask=None):
    d = df if mask is None else df[mask]
    kmf = KaplanMeierFitter().fit(d["os_years"], d["os_event"])
    return round(float(kmf.predict(years)) * 100)

rows = [("All patients", len(df), alive_pct(5), alive_pct(10))]
for s in ["I", "II", "III", "IV"]:
    m = df["stage_group"] == s
    rows.append((f"Stage {s}", int(m.sum()), alive_pct(5, m), alive_pct(10, m)))
for st in ["HR+/HER2-", "HER2-positive", "Triple Negative"]:
    m = df["molecular_subtype"] == st
    rows.append((st, int(m.sum()), alive_pct(5, m), alive_pct(10, m)))

out = pd.DataFrame(rows, columns=["Group", "N", "Alive at 5 yrs (%)", "Alive at 10 yrs (%)"])
out.to_csv(Path("reports/survival_rates.csv"), index=False)
print(out.to_string(index=False))
