# 01 — What we're downloading and why

Read this before you download. It's short.

## What is GDC

GDC stands for Genomic Data Commons. It's a website run by the US National Cancer Institute. You can go there and download real cancer patient data for free.

The website is [portal.gdc.cancer.gov](https://portal.gdc.cancer.gov).

Some files on GDC need a special application to download (mostly raw DNA sequencing). The files we want don't. Ours are fully open.

## What is TCGA

TCGA stands for The Cancer Genome Atlas. It's a big cancer research project that ran from about 2006 to 2018. Researchers collected data from more than 11,000 real cancer patients across 33 different cancer types.

All that data now lives on GDC.

## What we want, specifically

We want the breast cancer patients from TCGA. That group is called **TCGA-BRCA**. About 1,100 real patients.

For each patient we want:
- Their basic info (age, sex)
- Their diagnosis (what kind of breast cancer, what stage)
- What treatment they got
- Whether they're alive or dead, and if dead, when they died
- Any follow-up visits after diagnosis

We do **not** want their DNA data, imaging files, or lab samples. That would explode the download size and we don't need it for a survival analysis.

## What "survival endpoints" means

An endpoint is a way of measuring "how long did this patient do OK." There are four common ones for cancer:

- **Overall Survival (OS)** — how long from diagnosis until the patient died (from any cause).
- **Progression-Free Interval (PFI)** — how long until the cancer got worse, or came back, or the patient died.
- **Disease-Free Interval (DFI)** — how long until the cancer came back, for patients who had gotten to a "clean" state.
- **Disease-Specific Survival (DSS)** — how long until the patient died specifically from the cancer.

For breast cancer, OS and PFI are the two reliable ones. We'll focus on those.

There's a famous 2018 paper by Liu and colleagues in the journal *Cell* that laid out these definitions for TCGA data. Everyone doing survival analysis on TCGA cites it. We will too.

## The mapping challenge (why this project is different from your first two)

The TCGA data does not come in the CDISC clinical trial format (SDTM/ADaM). It's in its own format that the researchers made up years ago.

In real pharma jobs, a clinical data analyst often has to take data that came from somewhere else — an old trial, a hospital, an external company — and reshape it into the CDISC standard. That way it fits the rest of the company's tools.

**That's what this project shows off.** We take real breast cancer data in its raw format and turn it into proper SDTM domains (DM, MH, CM, DS). Nobody else in the "junior CDA with a portfolio" pile is doing this.

## What we'll actually build

1. Download the raw breast cancer files from GDC.
2. Load them into Python.
3. Reshape them into SDTM format (DM = demographics, MH = medical history, CM = medications, DS = disposition).
4. Run quality checks on them (same idea as your Project 1 QC engine).
5. Derive ADaM datasets (ADSL for the subject-level, ADTTE for time-to-event).
6. Do the survival analysis in R — Kaplan-Meier curves, log-rank test, Cox regression.
7. Build a Streamlit dashboard to show it all.

## Next step

Download the data. See the click-by-click instructions I gave in chat, or come back and ask.

Once the files are on your laptop, the next doc (`docs/02_first_look_at_the_data.md`) will open one file with you and explain what's inside.

## Sources

- [NCI Genomic Data Commons Portal](https://portal.gdc.cancer.gov)
- [Liu J et al., *An Integrated TCGA Pan-Cancer Clinical Data Resource*, Cell 2018](https://www.cell.com/cell/fulltext/S0092-8674(18)30229-0)
