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

## 2026-08-10 — Day 1 (cont.): GitHub, ER analysis, R reproduction

### What I built

- Committed the project and pushed to GitHub (public) with `gh repo create`.
- `src/07_survival_by_er.py` — survival by ER (estrogen receptor) status.
- `R/05_survival_by_stage.R` — reproduced the by-stage survival analysis in R with `survival` + `survminer`. Saved `reports/figures/km_by_stage_R.png`.

### What I learned

- **Local commit vs GitHub are different.** `git commit` only saves on my laptop. Nothing is online until I create a remote repo and push. GitHub Desktop only shows repos I add to it by hand.
- **Same answer in two languages.** The R log-rank p-value (p < 0.0001) matched Python. Showing both proves I'm not tied to one tool — useful for clinical roles that ask for R.
- **R survival vocabulary:** `Surv()` bundles time + event, `survfit()` fits KM curves, `survdiff()` is the log-rank test, `ggsurvplot()` draws curves + at-risk table + p-value.
- The R at-risk table made the thin-tail limitation concrete: by year 15 only 1-3 patients remain per group.

### Next

Item 3: map the raw data into CDISC SDTM domains (DM first, then MH, CM, DS). This is the differentiator.

---

## 2026-08-10 — Day 1 (cont.): SDTM mapping — DM domain

### What I built

- `src/08_sdtm_dm.py` — maps the raw patient data into the SDTM DM (Demographics) domain, saved to `data/processed/sdtm_dm.csv` (1,097 subjects).
- `docs/03_sdtm_mapping_spec.md` — the mapping specification: every DM variable, its source, its rule, and the reason.

### What SDTM is (interview version)

SDTM = Study Data Tabulation Model. It is the standard table format regulators (e.g. FDA) expect for clinical data. Data is split into **domains** — one table per topic — with fixed variable names AND fixed allowed values, so any reviewer can read any study the same way. Key domains: DM (demographics), MH (medical history), CM (medications), DS (disposition).

### The DM decisions I must be able to defend

- **SEX coded `F`/`M`, not "FEMALE"/"MALE".** SDTM uses *controlled terminology* — a fixed list of allowed values per variable. This is the heart of SDTM: standard column names AND standard values inside them.
- **RACE / ETHNIC left unchanged — on purpose.** TCGA already uses CDISC terms (`WHITE`, `NOT HISPANIC OR LATINO`). I checked against the standard first, then decided no change was needed. Checking and deciding "no change" is real mapping work, not skipping it.
- **USUBJID = the barcode.** It must be unique per subject. Every other domain reuses the same USUBJID so all of a subject's records tie back to one DM row. This is how the domains link.
- **DM has all 1,097 subjects, not the 1,035 analysis cohort.** DM describes everyone enrolled. Dropping short follow-up was an *analysis* decision, separate from demographics.

### Honest limitations (say these before they ask)

- TCGA gives day offsets, not calendar dates, so SDTM date variables (RFSTDTC etc.) are omitted.
- No ARM/ARMCD — TCGA is observational, not a randomized trial with treatment arms.

### Why this is a real skill, not "AI ran a script"

Real SDTM work IS mostly renaming and recoding against a rulebook, plus documenting each decision. The value is judgment and standards knowledge, not clever code. The deliverable a CDA hands over is the mapping spec, not the script. My defense is being able to explain every row of that spec.

### Next

CM (medications) domain — the more interesting reshape, because it is one row per drug (many per subject) and needs a sequence number (CMSEQ).

### CM and DS domains (added same day)

- `src/09_sdtm_cm.py` → CM (medications). One row per drug; `CMSEQ` numbers drugs 1..n per subject because USUBJID alone is not unique in CM. Key = USUBJID + CMSEQ.
- `src/10_sdtm_ds.py` → DS (disposition). One row per subject; `DSDECOD` = `DEATH`/`ALIVE`, the disposition version of the survival event flag. Counts match (104/993).

### "Are we CDISC compliant?" — the honest interview answer

No. This is a credible, documented SDTM mapping (DM, CM, DS) that demonstrates the skill. Full compliance needs: all domains and required variables, full controlled-terminology conformance (my `ALIVE` term would fail), a `define.xml` metadata file, and passing an automated checker (Pinnacle 21). Correct claim: "mapped to SDTM DM/CM/DS following CDISC conventions, deviations documented" — not "submission-ready." Knowing this difference is itself part of the skill.

---

## 2026-08-10 — Day 1 (cont.): subtypes, FISH refinement, Cox model

### What I built

- `src/11_derive_subtypes.py` — molecular subtype from ER/PR/HER2 IHC (HR+/HER2-, HER2-positive, Triple Negative, Unknown).
- `src/13_refine_subtypes_fish.py` — resolve equivocal/missing HER2 IHC using the FISH test (the real clinical tie-breaker). Cut Unknown from 356 to 129 (rescued 227).
- `src/12_survival_by_subtype.py` — KM survival by subtype.
- `src/14_cox_model.py` — multivariable Cox proportional-hazards model: age + stage + subtype together.
- `docs/04_analysis_plan.md` — full analysis roadmap (this is a big, multi-module project).

### The key clinical concepts

- **HER2 IHC vs FISH.** IHC is a protein stain (0/1+/2+/3+); 2+ is equivocal. FISH is a gene-copy test used to resolve equivocal IHC. Using FISH to rescue Unknowns mirrors the real lab workflow.
- **Molecular subtype** splits breast cancer into clinically distinct diseases: HR+/HER2- (best), HER2-positive, Triple Negative (worst).

### The Cox model — what it means and why it matters

- KM/log-rank tests one factor at a time; real factors are tangled (is worse survival from subtype or from stage?). Cox puts all factors in one model and gives each an effect **adjusted for the others**.
- **Hazard ratio (HR):** >1 = higher risk of death, <1 = lower, =1 = no effect. Reference groups here are Stage I and HR+/HER2-.
- **Results:** Stage IV HR ~4.4, Triple Negative ~3.0, Stage III ~2.6, HER2-positive ~2.2, age ~1.5 per decade, Stage II not different from Stage I. Stage and subtype each raise risk **independently**.

### The two findings I can defend

1. **Adjusted analysis separates tangled causes.** Subtype still matters after holding stage constant. Single KM charts cannot show this.
2. **Data cleaning changed the conclusion.** Before FISH refinement, raw KM made HER2-positive look worst. After refinement, Triple Negative is worst (HR 3.0) — the clinically correct answer. Cleaning fixed the science, not just the numbers.

### Also learned

- **Idempotent scripts.** Script 13 crashed on a second run because it re-merged a column it had already added (pandas made `_x`/`_y` copies). Fix: drop the helper columns before merging so re-running is safe. Pipeline scripts must be safe to run repeatedly.

### Cox assumption check + time-varying effects (same day)

- `src/15_cox_period_split.py` — after the Schoenfeld test flagged age, Stage IV, and Triple Negative as non-proportional, I estimated hazard ratios separately for years 0-5 vs 5+.
- **Result:** risk is front-loaded. Triple Negative HR 4.76 (years 0-5) then 0.63 (years 5+). Nearly all effects collapse toward 1 after 5 years. Matches known biology (Triple Negative recurs early or not at all).
- **Caveat I must state:** late period is tiny (83 patients, 14 deaths), so late HRs are unstable (Stage IV `0.00` is degenerate). The direction is robust; the exact late numbers are not.
- **Interview point:** I checked the model's assumption, found it violated, and turned the violation into a clinical finding instead of hiding it.

### Next (from docs/04 plan)

Table 1 cohort summary; then the Streamlit dashboard. Still open: PFI second endpoint, follow-up merge, MH domain, forest-plot polish.

## 2026-08-11 — Day 2: follow-up reconciliation changed the results

### What I found and fixed

- `src/18_reconcile_followup.py` — audited follow-up completeness. Our survival used the patient file alone. Found **779/1097 patients had later follow-up in the follow-up files**, and **48 "Alive" patients had actually died** (recorded only in follow-up).
- Reconciled all four sources (patient + three follow-up versions) to each patient's latest known status. Rebuilt the whole pipeline (`src/02` now reads the reconciled survival). Deaths 104 → 152; median follow-up 1.0 → 2.1 years.

### How the conclusions changed (this is the key story)

- Re-ran everything on corrected data. Cox model (penalized, 923 patients, 100 deaths): Age HR 1.23, Stage IV 6.70, Stage III 1.64 — stage and age are the strong predictors. Subtype now weak: Triple Negative only borderline (HR 1.44, p=0.057), HER2-positive not significant.
- The proportional-hazards assumption **now holds**. The earlier dramatic "front-loaded risk / Triple Negative HR 4.8" finding was largely an **artifact of the broken follow-up**.
- **Lesson to tell in interviews:** incomplete data gave a confident wrong story; fixing data completeness gave a quieter, truer, more conservative result. I found the flaw by auditing, not by luck.

### Also learned

- A Cox model can fail to converge ("singular matrix / high collinearity") when a group is lopsided after a data change. Fix: a small ridge `penalizer=0.1` stabilises it.
- Why I missed it first: I built survival from the patient file's own columns, which had zero missing values, so it looked complete. I did not cross-check the follow-up files. Combining all sources should have been the default for a survival study.

### Next

Commit corrected pipeline. Then: recurrence/progression endpoint from new-tumor-event data; reproducibility (requirements.txt + run-all); dashboard v2 leading with the headline.

---

<!--
Template for future entries — copy and fill in:

## YYYY-MM-DD — one-line summary of what got done

### What I built

### Why I did it that way

### What went wrong / what I had to fix

### What I learned

-->
