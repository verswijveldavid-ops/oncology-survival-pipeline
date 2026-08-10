# Learning log — Oncology Survival Pipeline

A running, dated log of what got built, what got decided, and what I learned. Kept from day one so the reasoning behind every choice is preserved and I can talk about it in interviews.

---

## 2026-08-10 — Day 1: project genesis

### Why this project exists

I already have two portfolio projects:

1. **clinical-data-pipeline** — CDISC SDTM Pilot (Xanomeline / Alzheimer's), synthetic data, end-to-end SDTM → QC → ADaM → safety analysis.
2. **rwe-omop-pipeline** — Real-world evidence on Eunomia OMOP dataset (synthetic GI bleed / NSAID safety signal).

Both are on synthetic data. Recruiters and hiring managers see a lot of synthetic-data portfolios. To differentiate, I want a third project on **real de-identified patient data**, in **oncology** (the largest single therapeutic hiring area in pharma), demonstrating a skill my first two projects don't: **survival analysis** and **mapping non-CDISC data into the CDISC standard**.

### Data source decision

I researched what's freely accessible today. Candidates:

| Source | Tradeoff | Chose? |
|---|---|---|
| Project Data Sphere | Real Phase III sponsor-donated data, ~250,000 patients, but needs free registration approval | Later (v2 upgrade) |
| NCI GDC / TCGA open clinical tier | Real ~11,000 cancer patients across 33 cancer types, zero registration for clinical data, includes survival endpoints | **Yes** |
| cBioPortal | Real, mostly open, but many good studies (like AACR GENIE) still need Synapse registration | No — GDC is more direct |
| KMDATA | Reconstructed IPD from 153 oncology trials, published paper supplement | Interesting — hold for later |
| SEER | Real cancer registry, huge, but not trial-structured and requires DUA | No — different flavor |
| openFDA FAERS | Real adverse events, no auth, but pharmacovigilance format not trial format | No — different project |

I picked **TCGA-BRCA** (breast invasive carcinoma, ~1,100 patients) via NCI GDC because:

- Real de-identified cancer patients — no synthetic data
- Zero registration required for the clinical supplement tier
- Survival endpoints already curated by Liu et al. (Cell 2018) so I can validate my derivations
- Breast cancer is a common oncology trial therapeutic area — knowledge transfers directly to job interviews
- ~1,100 patients is large enough to be interesting, small enough to iterate fast
- **The data is NOT in CDISC format** — this forces the mapping challenge that differentiates the project

### The mapping challenge — why this is the point

Real CDA work often involves data that didn't originate in a CDISC-compliant EDC:

- Legacy trials from before SDTM was mandatory
- Real-world data from EHRs, registries, or claims databases
- External cohorts acquired via licensing or M&A
- Investigator-initiated trials in academic EDCs (REDCap, OpenClinica)

In every case, someone has to **map the non-CDISC data into SDTM** so it can be analyzed with the same downstream tooling and, if needed, submitted to regulators. That someone is typically a CDA or a data engineer working with a CDA. If I can demonstrate the mapping skill on real data, I'm showing an ability my two previous projects didn't test.

### Today's actions

- Created project folder: `oncology-survival-pipeline/` with subfolders `data/{raw,processed}`, `src/`, `sql/`, `R/`, `docs/`, `app/`.
- Wrote `.gitignore` protecting personal files and raw downloaded data.
- Wrote `README.md` explaining the project intent, data source, pipeline architecture, tech stack.
- Started this log.
- Next: write `docs/01_gdc_and_tcga_orientation.md` explaining GDC/TCGA concepts before downloading, then walk through the actual GDC portal download.

### What I learned today

- **The difference between "open" and "no friction":** many "open" data sources still gate access behind a DUA, an ethics-committee statement, or a research proposal. GDC's clinical supplement tier is the rare case that is fully open — anyone can download the XML, no forms.
- **Why sponsors treat real patient-level trial data so carefully:** even de-identified, real patient data can be re-identified with enough linkage. That's why Project Data Sphere, YODA, Vivli, and CSDR all layer some approval process on top of "free." GDC clinical is possible because TCGA participants gave broad consent up front and the data was aggressively de-identified before public release.
- **The TCGA Pan-Cancer Clinical Data Resource (Liu et al., 2018)** is the standard reference for how to interpret TCGA's clinical endpoints. Anyone doing survival analysis on TCGA data cites it. It defines OS, PFI, DFI, DSS and warns about which cancer types have unreliable follow-up for which endpoints. Reading it before deriving ADTTE.

---

## 2026-08-10 — Day 1 (cont.): first look at the raw data

### What I did

Downloaded the TCGA-BRCA clinical data from GDC in BCR Biotab format. Unpacked the tarball into `data/raw/`. Then looked at the files together with Claude before writing any code.

### What's in the download

Ten tab-separated data files, each in its own UUID subfolder, plus a repeated `annotations.txt` and a `MANIFEST.txt` receipt.

- `clinical_patient_brca.txt` — the main file. One row per patient.
- `clinical_drug_brca.txt` — drugs given (many rows per patient).
- `clinical_radiation_brca.txt` — radiation treatments.
- `clinical_follow_up_v1.5 / v2.1 / v4.0_brca.txt` — follow-up visits, split across three form versions.
- `clinical_nte_brca.txt` + `clinical_follow_up_v4.0_nte_brca.txt` — new tumor events (cancer returned/new).
- `clinical_omf_v4.0_brca.txt` — other malignancies.

### The main patient file

1,097 patients, 112 columns.

### What I learned

- **Three header rows, not one.** Row 1 = short names, row 2 = alternate names, row 3 = CDE_ID codes. Data starts on row 4. A loader must skip rows 2–3 or every number turns into text. This is the classic Biotab gotcha.
- **The survival columns:** `vital_status` (993 Alive, 104 Dead), `death_days_to` (dead), `last_contact_days_to` (alive). A patient has one or the other, never both. Living patients are "censored" — we only know they survived up to their last visit.
- **Age is stored oddly:** `birth_days_to` is negative days from diagnosis back to birth.
- **Follow-up is split across three form versions** — merging them will be a task.
- **Data-quality flags already visible:** `Stage X` = unknown stage (not a real stage), and there is one male patient in an otherwise female cohort.

### Next

Once I confirm I understand the raw data, write the first Python script in `src/` to load all the biotab files into pandas, handling the 3-row header correctly.

---

## 2026-08-10 — Day 1 (cont.): built the clean patient table

### What I built

`src/01_load_biotab.py` — loads all 9 raw Biotab files into pandas, skipping the two junk header rows. Prints a size summary.

`src/02_build_patient_table.py` — builds one clean row per patient and saves it to `data/processed/patients.csv`. Done in four steps:

1. **Backbone** — read the patient file, keep 12 useful columns out of 112.
2. **Survival columns** — `os_time` (days followed) and `os_event` (1 = died, 0 = alive/censored). Rule: dead patient uses death day, living patient uses last-contact day.
3. **Squeeze + glue treatments** — grouped the drug and radiation files down to one row per patient, then merged onto the backbone: `n_drugs`, `got_chemo`, `got_hormone`, `got_radiation`.
4. **Save** — wrote the result to CSV so it persists and I can open it in a spreadsheet.

### What I learned

- **Grain** = what one row stands for. Patient file = one row per person. Drug file = one row per drug (our example patient had 6). The barcode `TCGA-...` is the thread that ties every file back to one person.
- **Squeeze = group by; glue = merge.** Collapse the many-rows-per-patient files into a summary, then attach by barcode. A left merge keeps all 1,097 patients even if they have no drug/radiation rows.
- **Censoring:** a living patient's survival is unknown past their last visit; event = 0 keeps that partial info instead of dropping it.
- **A script vs a data file are different things.** The `.py` is the recipe; it rebuilds the table in memory each run and throws it away. Saving to CSV is what makes the data persist.

### First real findings (of 1,097 patients)

- 993 alive, 104 died.
- 584 got chemotherapy, 523 hormone therapy, 528 radiation.

### Next

Stop 4 — quality checks. Then a first survival curve. Still to clean: `Stage X` (unknown stage) and the ER/PR/HER2 subtype columns.

---

## 2026-08-10 — Day 1 (cont.): quality checks + first survival curves

### What I built

- `src/03_quality_checks.py` — a CDA-style edit-check engine. Seven categories: missing, validity, consistency, timeline, controlled terms, uniqueness, referential (cross-file). Writes `data/processed/dq_issues.csv`.
- `src/04_build_analysis_table.py` — applies my documented decisions and writes `data/processed/patients_analysis.csv` (1,035 patients).
- `src/05_survival_km.py` — overall Kaplan-Meier curve for the whole cohort.
- `src/06_survival_by_stage.py` — Kaplan-Meier by stage, log-rank test, numbers-at-risk table.
- `docs/02_survival_findings.md` — the result and, importantly, the limitation.

### Data-quality decisions (documented, defensible)

- Dropped 62 patients with follow-up time <= 0 (2 negative, 60 zero). No usable survival info; matches Liu et al. 2018.
- Labelled unknown stage as "Unknown" instead of dropping the patient.
- Checks came back clean on consistency, referential integrity, uniqueness, missing, gender — so the only real issues were the time fields and unknown stage.

### The finding I care about

Survival falls as stage rises (Stage I best, IV worst) and the log-rank test says it's real. But the curves are **not equally trustworthy across time**. Small groups (Stage IV, n=20) and the tail past ~10 years rest on very few patients, so they take big steps and wobble. I kept the full timeline and added a numbers-at-risk table so the reader can see where the data thins out. Stating this limitation is the point, not hiding it.

### What I learned

- **A quality check flags, it doesn't fix.** In a real trial you'd query the site to correct a bad value. This is archived data, so the honest move is documented removal.
- **Kaplan-Meier handles censoring.** It uses living patients' partial follow-up instead of throwing it away.
- **"Number at risk" is everything.** Step size = one death / patients still followed. Few patients left = big, shaky steps.
- **Save figures outside the gitignored `data/` folder** (`reports/figures/`) so they show up on GitHub.

### Next

Reproduce the survival analysis in R (for the R skills the portfolio needs). More comparisons: survival by ER status and by treatment. Then the Streamlit dashboard. Later: SDTM mapping (DM, MH, CM, DS) as the CDISC-standard showcase.

---

<!--
Template for future entries — copy and fill in:

## YYYY-MM-DD — one-line summary of what got done

### What I built

### Why I did it that way

### What went wrong / what I had to fix

### What I learned

-->
