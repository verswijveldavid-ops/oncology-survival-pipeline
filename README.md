# Oncology Survival Pipeline — TCGA-BRCA

End-to-end clinical data pipeline on **real-world oncology data**: map the TCGA breast cancer cohort into CDISC SDTM/ADaM standard, run data quality checks, derive time-to-event analysis datasets, perform Kaplan-Meier and Cox regression survival analysis, and publish an interactive dashboard.

## Why this project

Most junior clinical data analyst portfolios use synthetic CDISC data. This one uses **real de-identified patient data from the NCI Genomic Data Commons** (~1,100 real breast cancer patients from the TCGA-BRCA study), and demonstrates the CDA skill of **mapping non-CDISC real-world data into the CDISC standard** — a task every sponsor faces when integrating legacy data, external cohorts, or acquired assets.

## Data source

- **Repository:** NCI Genomic Data Commons ([portal.gdc.cancer.gov](https://portal.gdc.cancer.gov))
- **Program:** The Cancer Genome Atlas (TCGA)
- **Project:** TCGA-BRCA (Breast Invasive Carcinoma)
- **Access tier:** Open (no registration for clinical supplement data)
- **Cohort size:** ~1,100 patients
- **Endpoints available:** Overall Survival (OS), Progression-Free Interval (PFI), Disease-Free Interval (DFI), Disease-Specific Survival (DSS) — as standardized by [Liu et al., Cell 2018 (TCGA Pan-Cancer Clinical Data Resource)](https://www.cell.com/cell/fulltext/S0092-8674(18)30229-0)

The raw XML/tab-delimited files are **not committed to the repo** — they are re-downloadable from GDC using the manifest saved in `data/raw/manifest.txt`.

## Pipeline architecture

```
data/raw/                  Raw XML + biotabs from GDC (gitignored)
   ↓  01_load_and_flatten.py
data/processed/patients.parquet    One-row-per-patient dataframe
   ↓  02_map_to_sdtm.py
data/processed/sdtm_*.parquet      DM, MH, CM, DS domains
   ↓  03_quality_checks.py + sql/  Edit-check engine (extends Project 1 pattern)
data/processed/dq_issues.csv       Flagged issues per dimension
   ↓  R/04_derive_adam.R           ADSL + ADTTE
data/processed/adam_*.parquet
   ↓  R/05_survival_analysis.R     KM curves, log-rank, Cox
data/processed/km_results.parquet
   ↓  app/app.py                   Streamlit dashboard
```

## Tech stack

- **Python 3.11+** (pandas, DuckDB, lxml) — data loading, SDTM mapping, QC
- **SQL** (via DuckDB) — edit checks
- **R 4.3+** (admiral, survival, survminer, ggplot2) — ADaM derivation, survival analysis
- **Streamlit + Altair** — dashboard

## Repository structure

- `data/` — raw and processed data (contents gitignored, folders tracked with .gitkeep)
- `src/` — Python scripts (numbered in pipeline order)
- `sql/` — SQL queries for the DuckDB-based QC engine
- `R/` — R scripts for ADaM derivation and survival analysis
- `docs/` — orientation notes, mapping decisions, methods writeups
- `app/` — Streamlit dashboard
- `learning_log.md` — running log of what was built, why, what was learned

## Status

**Started:** 2026-08-10. In progress.
