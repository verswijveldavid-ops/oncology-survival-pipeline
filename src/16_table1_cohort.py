"""
16_table1_cohort.py
Build "Table 1": a summary of who is in the cohort, split by outcome
(Alive vs Dead). This is the standard opening table of a clinical study.
Run from the project root:  python3 src/16_table1_cohort.py
"""
from pathlib import Path
import pandas as pd

df = pd.read_csv(Path("data/processed/patients_analysis.csv"))

# Treatment flags may load as text "True"/"False"; make them real booleans.
def as_bool(s):
    return s.astype(str).str.lower().isin(["true", "1", "yes"])

for col in ["got_chemo", "got_hormone", "got_radiation"]:
    df[col] = as_bool(df[col])

# Three columns: everyone, the living, the dead.
groups = {
    "Overall": df,
    "Alive": df[df["vital_status"] == "Alive"],
    "Dead": df[df["vital_status"] == "Dead"],
}

rows = []

def blank_header(text):
    rows.append({"Characteristic": text, "Overall": "", "Alive": "", "Dead": ""})

def count_row(value, column):
    r = {"Characteristic": f"  {value}"}
    for name, g in groups.items():
        n = int((g[column] == value).sum())
        r[name] = f"{n} ({100 * n / len(g):.0f}%)" if len(g) else "0"
    rows.append(r)

def bool_row(label, column):
    r = {"Characteristic": label}
    for name, g in groups.items():
        n = int(g[column].sum())
        r[name] = f"{n} ({100 * n / len(g):.0f}%)" if len(g) else "0"
    rows.append(r)

# Count of patients.
rows.append({"Characteristic": "N (patients)",
             **{name: str(len(g)) for name, g in groups.items()}})

# Age as median with the middle 50% range.
r = {"Characteristic": "Age, median [Q1-Q3]"}
for name, g in groups.items():
    a = g["age_at_diagnosis"].dropna()
    r[name] = f"{a.median():.0f} [{a.quantile(.25):.0f}-{a.quantile(.75):.0f}]"
rows.append(r)

blank_header("Sex, n (%)")
for v in ["FEMALE", "MALE"]:
    count_row(v, "gender")

blank_header("Stage, n (%)")
for v in ["I", "II", "III", "IV", "Unknown"]:
    count_row(v, "stage_group")

blank_header("Molecular subtype, n (%)")
for v in ["HR+/HER2-", "HER2-positive", "Triple Negative", "Unknown"]:
    count_row(v, "molecular_subtype")

blank_header("Treatment, n (%)")
bool_row("  Chemotherapy", "got_chemo")
bool_row("  Hormone therapy", "got_hormone")
bool_row("  Radiation", "got_radiation")

table1 = pd.DataFrame(rows, columns=["Characteristic", "Overall", "Alive", "Dead"]).fillna("")
table1.to_csv(Path("reports/table1_cohort.csv"), index=False)
print(table1.to_string(index=False))
