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

## Data-completeness fix (important — it changed the results)

Our first survival table used the patient file alone. An audit found that **779 of 1,097 patients had later follow-up recorded in the follow-up files** we had ignored, and **48 patients marked "Alive" had actually died** (recorded only in a follow-up file). We reconciled all four sources (patient file + three follow-up versions), taking each patient's latest known status.

Effect: deaths rose 104 → 152; median follow-up for living patients doubled (1.0 → 2.1 years). **Every result below uses the corrected data.** The earlier, patient-file-only numbers were biased and are superseded.

## Multivariable model (corrected data)

Cox proportional-hazards model with age, stage, and subtype together (ridge-penalized for stability), on 923 patients with 100 deaths:

| Factor | HR | p |
|---|---|---|
| Age (per decade) | 1.23 | <0.001 |
| Stage II | 0.88 | 0.41 (ns) |
| Stage III | 1.64 | 0.006 |
| Stage IV | 6.70 | <0.001 |
| HER2-positive | 1.15 | 0.46 (ns) |
| Triple Negative | 1.44 | 0.057 (borderline) |

Concordance 0.79. **Stage and age are the strong independent predictors.** After adjustment on the corrected data, subtype's independent effect is weak — Triple Negative is only borderline, HER2-positive not significant.

## What changed vs the broken-data analysis

On the truncated data we had reported a dramatic "front-loaded risk" pattern (Triple Negative HR ~4.8 early, dropping later) and a violated proportional-hazards assumption. **With corrected follow-up, the proportional-hazards assumption now holds** (no variable clearly fails it), and the time-varying pattern is only a weak, non-significant hint. The earlier finding was largely an artifact of missing follow-up.

**The lesson:** a data-completeness problem produced a confident but wrong story. Fixing it gave a quieter, more conservative, more trustworthy result. This is the single most important methodological point in the project.

## Sources

- [Liu J et al., *An Integrated TCGA Pan-Cancer Clinical Data Resource*, Cell 2018](https://www.cell.com/cell/fulltext/S0092-8674(18)30229-0)
