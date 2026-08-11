# Breast Cancer Survival — TCGA-BRCA

**Who lives longer after a breast cancer diagnosis, and why?**

An end-to-end clinical data pipeline on **real, de-identified patient data**: clean the data, check it, run a survival analysis, standardise it into the drug industry's CDISC formats (SDTM and ADaM), and present the findings in an interactive dashboard.

> ▶ **Live dashboard:** https://oncology-survival-pipeline-husupmr7t8azdx3xjdbc9p.streamlit.app/

---

## Why this project is different

Most beginner portfolios use made-up data. This one uses **real, anonymous data on ~1,100 breast cancer patients** from the public [NCI Genomic Data Commons](https://portal.gdc.cancer.gov) (the TCGA-BRCA study). It also does something those portfolios skip: it maps non-standard real-world data **into the CDISC standard** that every drug sponsor uses — and it does the survival statistics on top.

## The headline finding

| Group | 5-year survival | 10-year survival |
|---|---|---|
| All patients | 82% | 58% |
| Stage I (earliest) | 90% | 80% |
| Stage IV (most advanced) | 27% | 9% |

After weighing everything at once (a Cox model), **how far the cancer has spread (stage) and the patient's age are the strongest drivers of survival.** Cancer subtype mattered less once stage and age were accounted for.

## The best story: I found and fixed a data error

My first version read only one file to decide who lived or died. It was incomplete. Combining **all** the follow-up records revealed that **48 patients marked "alive" had actually died**, and follow-up time roughly doubled. This changed the results — an earlier "dramatic" finding turned out to be an artifact of the missing data. Finding and correcting it is the core of careful clinical data work.

## The pipeline

```
raw files  →  reconcile all follow-up records  →  clean patient table
   →  quality checks  →  analysis table (subtypes via IHC + FISH)
   →  survival analysis (Kaplan-Meier, Cox)  →  SDTM (DM, CM, DS)
   →  ADaM (ADSL, ADTTE with admiral)  →  dashboard
```

This is the full regulatory chain: **raw data → SDTM → ADaM → analysis.**

## Tech stack

- **Python** — pandas, lifelines (survival analysis), matplotlib.
- **R** — survival, survminer, and **admiral** (the industry ADaM tool).
- **Streamlit** — the interactive dashboard.

## How to run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/app.py
```

The raw patient files are re-downloadable from the GDC portal (BCR Biotab format, TCGA-BRCA clinical). The processed analysis table is included so the dashboard runs immediately.

## Honest limits

- The far end of each survival curve rests on very few patients, so it is less reliable.
- Cancer subtype is missing for some patients (recovered where possible using the FISH test).
- Recurrence is thinly recorded, so the progression-free endpoint adds little here.
- The CDISC mapping demonstrates the standard but is not full submission compliance (deviations are documented in `docs/`).

## Repository

- `src/` — Python scripts, numbered in pipeline order.
- `R/` — R scripts (survival analysis, ADaM datasets).
- `docs/` — orientation, survival findings, SDTM mapping spec, analysis plan.
- `app/` — the Streamlit dashboard.
- `reports/` — figures and result tables.
- `learning_log.md` — a dated record of what was built and why.

## Data source

NCI Genomic Data Commons, TCGA-BRCA (Breast Invasive Carcinoma). Open-access clinical tier. Survival endpoints follow [Liu et al., *Cell* 2018](https://www.cell.com/cell/fulltext/S0092-8674(18)30229-0).

---

*Educational portfolio project. Real de-identified data; findings demonstrate methodology and are not clinical advice.*
