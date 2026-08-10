# R/05_survival_by_stage.R
# Reproduce the by-stage Kaplan-Meier survival analysis in R.
# Run from the project root:  Rscript R/05_survival_by_stage.R

library(survival)
library(survminer)

df <- read.csv("data/processed/patients_analysis.csv")
df <- df[df$stage_group %in% c("I", "II", "III", "IV"), ]
df$stage_group <- factor(df$stage_group, levels = c("I", "II", "III", "IV"))

# Surv() = the time-to-event object: how long + did they die (1=yes).
# survfit() = fit the Kaplan-Meier curves, split by stage.
fit <- survfit(Surv(os_years, os_event) ~ stage_group, data = df)

# survdiff() = the log-rank test (are the curves really different?).
print(survdiff(Surv(os_years, os_event) ~ stage_group, data = df))

# ggsurvplot() = publication-style curves with a numbers-at-risk table.
p <- ggsurvplot(fit, data = df,
                risk.table = TRUE, pval = TRUE,
                legend.title = "Stage", legend.labs = c("I", "II", "III", "IV"),
                xlab = "Years from diagnosis", ylab = "Survival probability",
                title = "Overall Survival by Stage - TCGA-BRCA (R)")

png("reports/figures/km_by_stage_R.png", width = 900, height = 800, res = 120)
print(p)
dev.off()
cat("saved -> reports/figures/km_by_stage_R.png\n")
