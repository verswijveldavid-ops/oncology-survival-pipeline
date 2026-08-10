"""
01_load_biotab.py
-----------------
Step 1 of the pipeline: read the raw TCGA-BRCA files into pandas.

The raw files are in "BCR Biotab" format: plain tab-separated text.
Each file has THREE header rows, not one:
    row 1 = the column names we want
    row 2 = alternate names   (junk for us)
    row 3 = CDE_ID codes      (junk for us)
The real data starts on row 4.

If we don't skip rows 2 and 3, pandas treats them as data, and every
number column turns into text. So the whole job of this file is:
read each raw file, skip those two junk rows, and hand back a clean table.

Run it from the project root:
    python3 src/01_load_biotab.py
"""

from pathlib import Path
import pandas as pd

# Where the raw files live. This path is relative to the project root.
RAW_DIR = Path("data/raw")

# Values TCGA uses to mean "no answer". We turn these into real blanks (NaN)
# so pandas knows they are missing, not real text.
MISSING = [
    "[Not Available]",
    "[Not Applicable]",
    "[Unknown]",
    "[Not Evaluated]",
    "[Discrepancy]",
    "[Completed]",
]


def read_biotab(path: Path) -> pd.DataFrame:
    """Read one Biotab file into a clean DataFrame.

    - sep="\t"        the file is tab-separated
    - skiprows=[1, 2] skip the 2nd and 3rd lines (the junk header rows),
                      but keep the 1st line as the column names
    - dtype=str       read everything as text for now; we convert
                      specific columns to numbers later, on purpose
    - na_values       treat TCGA's "no answer" strings as missing
    """
    return pd.read_csv(
        path,
        sep="\t",
        skiprows=[1, 2],
        dtype=str,
        na_values=MISSING,
        keep_default_na=True,
    )


def find_biotab_files(raw_dir: Path) -> dict[str, Path]:
    """Find every Biotab data file under data/raw.

    GDC puts each file in its own random-named subfolder, so we search
    all subfolders. We skip annotations.txt and the manifest, which are
    not patient data. The key in the returned dict is a short nickname
    taken from the file name (e.g. "patient", "drug", "follow_up_v4.0").
    """
    files: dict[str, Path] = {}
    for path in sorted(raw_dir.rglob("nationwidechildrens.org_clinical_*_brca.txt")):
        # Turn "..._clinical_patient_brca.txt" into "patient".
        nickname = path.name.replace("nationwidechildrens.org_clinical_", "")
        nickname = nickname.replace("_brca.txt", "")
        files[nickname] = path
    return files


def load_all(raw_dir: Path = RAW_DIR) -> dict[str, pd.DataFrame]:
    """Load every Biotab file into a dict of DataFrames, keyed by nickname."""
    tables: dict[str, pd.DataFrame] = {}
    for nickname, path in find_biotab_files(raw_dir).items():
        tables[nickname] = read_biotab(path)
    return tables


if __name__ == "__main__":
    tables = load_all()

    print(f"Loaded {len(tables)} files from {RAW_DIR}/\n")
    print(f"{'file':22} {'rows':>6} {'cols':>6}")
    print("-" * 36)
    for nickname, df in tables.items():
        print(f"{nickname:22} {len(df):>6} {df.shape[1]:>6}")
