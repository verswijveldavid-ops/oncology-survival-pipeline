# R/06_build_adsl.R -- Build the ADaM ADSL (Subject-Level Analysis Dataset).
# ADSL = one row per subject: demographics, grouping vars, population flags.
# Run from the project root:  Rscript R/06_build_adsl.R
library(dplyr)

dm  <- read.csv("data/processed/sdtm_dm.csv", stringsAsFactors = FALSE)
ana <- read.csv("data/processed/patients_analysis.csv", stringsAsFactors = FALSE)

adsl <- dm %>%
  left_join(
    ana %>% select(USUBJID = bcr_patient_barcode,
                   STAGEGR1 = stage_group, SUBTYPE = molecular_subtype,
                   os_event, got_chemo, got_hormone, got_radiation),
    by = "USUBJID"
  ) %>%
  mutate(
    AGEGR1  = case_when(is.na(AGE) ~ NA_character_,
                        AGE < 50 ~ "<50", AGE < 70 ~ "50-69", TRUE ~ ">=70"),
    CHEMOFL = ifelse(got_chemo    %in% c("True", "TRUE"), "Y", "N"),
    HORMFL  = ifelse(got_hormone  %in% c("True", "TRUE"), "Y", "N"),
    RADFL   = ifelse(got_radiation %in% c("True", "TRUE"), "Y", "N"),
    DTHFL   = ifelse(!is.na(os_event) & os_event == 1, "Y", "N"),
    SAFFL   = "Y",   # safety population flag (everyone here)
    ITTFL   = "Y"    # intent-to-treat flag
  ) %>%
  select(STUDYID, USUBJID, SUBJID, SEX, AGE, AGEU, AGEGR1, RACE, ETHNIC,
         STAGEGR1, SUBTYPE, CHEMOFL, HORMFL, RADFL, DTHFL, SAFFL, ITTFL)

write.csv(adsl, "data/processed/adam_adsl.csv", row.names = FALSE)
cat("ADSL:", nrow(adsl), "subjects x", ncol(adsl), "variables\n")
cat("deaths (DTHFL=Y):", sum(adsl$DTHFL == "Y"), "\n")
print(head(adsl, 4))
