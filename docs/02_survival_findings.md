# 02 — Survival analysis: findings and limitations

Short notes on what the survival curves show, and where they can't be trusted.

## What we did

We built one clean row per patient. We derived two survival columns:

- **os_time** — how long we followed the patient.
- **os_event** — 1 if the patient died, 0 if still alive (censored).

We dropped 62 patients whose follow-up time was 0 or negative. Those give no usable survival information. This matches the standard TCGA guidance (Liu et al., Cell 2018). The analysis cohort is **1,035 patients**.

We then drew Kaplan-Meier survival curves, split by cancer stage.

## The main result

Survival drops as stage rises. Stage I patients do best. Stage IV do worst. This is the expected clinical pattern, which is a good sign that the pipeline is sound. The log-rank test (a check for whether the groups really differ) confirms the gap between stages is real, not chance.

## The limitation we want to be honest about

**The curves are not equally trustworthy across the whole timeline.**

A Kaplan-Meier curve steps down each time a patient dies. The size of each step depends on how many patients are still being followed at that moment. This count is the "number at risk."

- Early in follow-up, hundreds of patients are still at risk. Each death moves the curve only slightly. These parts are reliable.
- Late in follow-up, only a few patients remain. Each death moves the curve a lot. These parts are shaky.

This shows up two ways in our chart:

1. **Stage IV is a small group (only 20 patients).** Its curve takes big steps because each death is about 5% of the group. The final vertical drop to zero is simply the last patient dying, not a sudden mass death.
2. **The tail after about 10 years is thin for every group.** The curves wobble and cross there. That crossing is noise from a handful of patients, not real biology.

## How we handled it

We **kept the full timeline** rather than cutting it off. We added a **numbers-at-risk table** under the chart. The reader can see exactly where the data thins out and judge the curves accordingly.

**Rule of thumb for reading the chart:** trust a curve while its number at risk is still healthy. Treat small groups and the far-right tail as suggestive, not conclusive.

## Multivariable model and time-varying risk

We fitted a Cox proportional-hazards model with age, stage, and molecular subtype together. This adjusts each factor for the others. After adjustment, higher stage and worse subtype each raise the risk of death independently. Reference groups were Stage I and HR+/HER2-.

We then checked the model's core assumption (proportional hazards, via Schoenfeld residuals). Three variables failed it: age, Stage IV, and Triple Negative. Their effect on risk is **not constant over time**.

Rather than hide this, we investigated it. We estimated hazard ratios separately for the first 5 years and after 5 years:

| Factor | Years 0-5 | Years 5+ |
|---|---|---|
| Triple Negative | 4.76 | 0.63 |
| Stage IV | 7.51 | 0.00 (unstable) |
| HER2-positive | 3.04 | 0.95 |
| Stage III | 2.96 | 1.08 |
| Age (per decade) | 1.61 | 1.08 |

**Finding:** risk is front-loaded into the first 5 years. Triple Negative is about 4.8x the death rate early, then falls below the reference for patients who survive 5 years. This matches known biology: Triple Negative breast cancer recurs early or not at all.

**Limitation:** the late period has only 83 patients and 14 deaths, so the late hazard ratios are unstable (the Stage IV `0.00` is a degenerate estimate, not real). The trustworthy message is the direction — effects shrink sharply after 5 years — not the exact late numbers.

## Sources

- [Liu J et al., *An Integrated TCGA Pan-Cancer Clinical Data Resource*, Cell 2018](https://www.cell.com/cell/fulltext/S0092-8674(18)30229-0)
