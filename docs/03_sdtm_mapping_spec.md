# 03 — SDTM mapping specification

This is the plan for turning the raw TCGA data into CDISC SDTM domains. It lists, for each standard variable, where it comes from and the rule used. This is the artifact that proves the mapping was a set of decisions, not a guess.

SDTM = Study Data Tabulation Model. It is the standard table format regulators expect for clinical data. Data is split into **domains** — one table per topic — with fixed variable names so any reviewer can read any study the same way.

---

## DM — Demographics

**Grain:** one row per subject. Source file: patient file (all 1,097 subjects).

| SDTM variable | Meaning | Source (raw) | Rule |
|---|---|---|---|
| STUDYID | Study identifier | — | Fixed value `TCGA-BRCA` |
| DOMAIN | Domain code | — | Fixed value `DM` |
| USUBJID | Unique subject ID | `bcr_patient_barcode` | Copied as-is (e.g. `TCGA-3C-AAAU`) |
| SUBJID | Subject ID within study | `bcr_patient_barcode` | Last part after the final `-` |
| SEX | Sex | `gender` | `FEMALE` → `F`, `MALE` → `M` |
| AGE | Age | `age_at_diagnosis` | Copied as-is |
| AGEU | Age unit | — | Fixed value `YEARS` |
| RACE | Race | `race` | Copied as-is (already CDISC terms) |
| ETHNIC | Ethnicity | `ethnicity` | Copied as-is (already CDISC terms) |

### Decisions and reasons

- **SEX is coded `F`/`M`, not the full words.** SDTM uses controlled terminology — a fixed list of allowed values. For SEX the allowed codes are single letters. This is the core idea of SDTM: not just standard column names, but standard *values* inside them.
- **RACE and ETHNIC were left as-is on purpose.** TCGA already uses the CDISC-controlled terms (`WHITE`, `BLACK OR AFRICAN AMERICAN`, `NOT HISPANIC OR LATINO`). We checked before copying. Checking, then deciding no change is needed, is itself the mapping work.
- **USUBJID must be unique per subject.** The barcode is. Every other domain (CM, MH, DS) will use the same USUBJID so all of a subject's records link back to their DM row.
- **DM includes all 1,097 subjects**, not the 1,035 analysis cohort. DM describes everyone enrolled. The follow-up-time filtering was an analysis decision, not a demographics one.

### Known limitations (stated honestly)

- **No real dates.** TCGA gives day offsets from diagnosis, not calendar dates. So SDTM date variables like RFSTDTC (reference start date) are omitted. A real submission would need true dates.
- **ARM / ARMCD omitted.** TCGA is observational, not a randomized trial, so there are no treatment arms to assign.

---

## CM — Concomitant Medications

**Grain:** one row per drug (many per subject). Source file: drug file (2,406 rows).

| SDTM variable | Meaning | Source (raw) | Rule |
|---|---|---|---|
| STUDYID | Study identifier | — | Fixed value `TCGA-BRCA` |
| DOMAIN | Domain code | — | Fixed value `CM` |
| USUBJID | Unique subject ID | `bcr_patient_barcode` | Copied as-is; links to the DM row |
| CMSEQ | Sequence number within subject | — | Drugs numbered 1..n per subject, ordered by start day |
| CMTRT | Reported drug name | `pharmaceutical_therapy_drug_name` | Uppercased |
| CMCLAS | Drug class | `pharmaceutical_therapy_type` | Copied (e.g. `Chemotherapy`, `Hormone Therapy`) |
| CMSTDY | Study day of start | `pharmaceutical_tx_started_days_to` | Day offset from diagnosis |
| CMENDY | Study day of end | `pharmaceutical_tx_ended_days_to` | Day offset from diagnosis |

### Decisions and reasons

- **CMSEQ exists because USUBJID is not unique here.** A subject has many drug rows. SDTM identifies each record by USUBJID **plus** the sequence number. Without CMSEQ you could not point to one specific drug record.
- **Ordered by start day** so the sequence reads as the treatment timeline.
- **CMTRT uppercased** — a common convention that avoids "Cytoxan" vs "CYTOXAN" being treated as two drugs.

### Known limitations (stated honestly)

- **CMDECOD not populated.** In a real submission the reported drug name (CMTRT) is coded to a standardized preferred name using the WHO Drug Dictionary (a licensed medical dictionary). We have no access to it, so this step is flagged, not faked.
- **Day numbering.** SDTM study day (--DY) has no day 0 by convention; TCGA uses day 0 = diagnosis. We kept the raw offsets and note the difference rather than silently shifting them.

---

## DS — Disposition

**Grain:** one row per subject. Source file: patient file.

| SDTM variable | Meaning | Source (raw) | Rule |
|---|---|---|---|
| STUDYID | Study identifier | — | Fixed value `TCGA-BRCA` |
| DOMAIN | Domain code | — | Fixed value `DS` |
| USUBJID | Unique subject ID | `bcr_patient_barcode` | Copied as-is; links to the DM row |
| DSSEQ | Sequence number within subject | — | `1` (one disposition record per subject) |
| DSDECOD | Standardized disposition term | `vital_status` | `Dead` → `DEATH`, `Alive` → `ALIVE` |
| DSTERM | Reported disposition term | `vital_status` | `Dead` → `DEATH`, `Alive` → `ALIVE AT LAST CONTACT` |
| DSSTDY | Study day of the event | `death_days_to` / `last_contact_days_to` | Death day if dead, else last-contact day |

### Decisions and reasons

- **DSDECOD is the disposition version of the survival event flag.** `DEATH`/`ALIVE` mirrors `os_event` 1/0. Counts match: 104 DEATH, 993 ALIVE.
- **DSSTDY uses the either/or rule** — death day for the dead, last-contact day for the living — the same logic as `os_time`.

### Known limitations (stated honestly)

- **`ALIVE` is not a formal CDISC disposition term.** The controlled terminology for study disposition uses terms like `COMPLETED` and `ONGOING`. We use `DEATH`/`ALIVE` because this is a survival dataset, and flag the deviation rather than hide it.
- **Only the final outcome is captured.** A full DS domain would also record informed consent, study entry, and other disposition events. We map the survival-relevant outcome only.

---

## Are we "CDISC compliant"?

No — and stating this precisely matters. This is a **credible, documented SDTM mapping** of the main data, which demonstrates the mapping skill. Full submission compliance would additionally require: all applicable domains and required variables, full controlled-terminology conformance (the `ALIVE` deviation would fail), a `define.xml` metadata file, and passing an automated conformance checker (Pinnacle 21). The honest claim is "mapped to SDTM DM/CM/DS following CDISC conventions, with deviations documented" — not "submission-ready."
