# 04 — Analysis plan (the full scope)

This project is meant to be deep, like a real clinical study, not a single chart. Below is the full list of analyses this dataset supports. We work through them as modules. Done items are checked.

## A. Cohort characterization ("Table 1")

Every clinical paper starts here: describe who is in the cohort.

- [ ] Baseline characteristics table: age, sex, race, stage, subtype, treatment — split by vital status.
- [ ] Distributions: age histogram, stage bar chart, subtype breakdown.
- [ ] Treatment patterns: most common drugs, chemo vs hormone vs radiation.

## B. Molecular subtypes

Breast cancer is really several diseases. Derive the standard subtypes from ER, PR, HER2.

- [ ] Derive subtype: HR+/HER2−, HER2-positive, Triple Negative, Unknown.
- [ ] Subtype distribution across the cohort.

## C. Survival analysis — univariate (one factor at a time)

Kaplan-Meier + log-rank for each factor.

- [x] Overall survival (whole cohort).
- [x] By stage.
- [x] By ER status.
- [ ] By molecular subtype.
- [ ] By age group.
- [ ] By treatment (chemo / hormone / radiation).

## D. Survival analysis — multivariable

The real statistical centerpiece.

- [ ] Cox proportional hazards model: age + stage + subtype + treatment together, with hazard ratios and confidence intervals.
- [ ] Check the proportional-hazards assumption (Schoenfeld residuals).
- [ ] Forest plot of hazard ratios.

## E. Second endpoint — progression

Not just death. Use the new-tumor-event data.

- [ ] Derive Progression-Free Interval (PFI) from the new-tumor-event files.
- [ ] KM and Cox for PFI.
- [ ] Compare our derived endpoints against the Liu et al. 2018 curated values (validation).

## F. Data engineering / CDM depth

- [ ] Merge the three follow-up form versions (v1.5, v2.1, v4.0) into one follow-up table.
- [ ] Cross-domain edit checks (e.g. a drug that starts after the death date).
- [ ] Complete the SDTM set: add MH (medical history); consider a define-style metadata file.

## G. Delivery

- [ ] Streamlit dashboard tying the findings together.
- [ ] A written results summary (README-level), with the honest limitations.

---

Order is flexible. B and A feed C and D, so we do subtypes and characterization before the multivariable model.
