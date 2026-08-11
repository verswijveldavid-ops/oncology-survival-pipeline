# R/07_build_adtte.R -- Build ADaM ADTTE (Time-to-Event) with admiral.
# Endpoints: OS (Overall Survival) and PFS (Progression-Free Survival).
# Run from the project root:  Rscript R/07_build_adtte.R
library(admiral)
library(dplyr)

adsl <- read.csv("data/processed/adam_adsl.csv", stringsAsFactors = FALSE)
ana  <- read.csv("data/processed/patients_analysis.csv", stringsAsFactors = FALSE)

# Attach times/events and synthesise dates (day 0 = diagnosis at a fixed anchor).
anchor <- as.Date("2000-01-01")
adsl <- adsl %>%
  left_join(ana %>% select(USUBJID = bcr_patient_barcode,
                           os_time, os_event, pfi_years, pfi_event),
            by = "USUBJID") %>%
  filter(!is.na(os_time)) %>%
  mutate(
    STARTDT  = anchor,
    DTHDT    = if_else(os_event == 1, anchor + round(os_time), as.Date(NA)),
    LSTALVDT = anchor + round(os_time),
    PFSDT    = if_else(pfi_event == 1, anchor + round(pfi_years * 365.25), as.Date(NA)),
    PFSCNDT  = anchor + round(pfi_years * 365.25)
  )

# --- OS: event = death; censor = last known alive -----------------------
death_event  <- event_source(dataset_name = "adsl", filter = os_event == 1,
                             date = DTHDT, set_values_to = exprs(EVNTDESC = "DEATH"))
alive_censor <- censor_source(dataset_name = "adsl", date = LSTALVDT,
                             set_values_to = exprs(EVNTDESC = "LAST KNOWN ALIVE"))
adtte_os <- derive_param_tte(
  dataset_adsl = adsl, start_date = STARTDT,
  event_conditions = list(death_event), censor_conditions = list(alive_censor),
  source_datasets = list(adsl = adsl),
  set_values_to = exprs(PARAMCD = "OS", PARAM = "Overall Survival"))

# --- PFS: event = progression or death; censor = no progression ---------
pfs_event  <- event_source(dataset_name = "adsl", filter = pfi_event == 1,
                          date = PFSDT, set_values_to = exprs(EVNTDESC = "PROGRESSION OR DEATH"))
pfs_censor <- censor_source(dataset_name = "adsl", date = PFSCNDT,
                          set_values_to = exprs(EVNTDESC = "NO PROGRESSION"))
adtte_pfs <- derive_param_tte(
  dataset_adsl = adsl, start_date = STARTDT,
  event_conditions = list(pfs_event), censor_conditions = list(pfs_censor),
  source_datasets = list(adsl = adsl),
  set_values_to = exprs(PARAMCD = "PFS", PARAM = "Progression-Free Survival"))

adtte <- bind_rows(adtte_os, adtte_pfs) %>%
  derive_vars_duration(new_var = AVAL, start_date = STARTDT, end_date = ADT,
                       out_unit = "days", add_one = FALSE) %>%
  mutate(AVALU = "DAYS") %>%
  left_join(adsl %>% select(USUBJID, SEX, AGE, STAGEGR1, SUBTYPE), by = "USUBJID") %>%
  select(STUDYID, USUBJID, PARAMCD, PARAM, STARTDT, ADT, AVAL, AVALU, CNSR,
         EVNTDESC, SEX, AGE, STAGEGR1, SUBTYPE)

write.csv(adtte, "data/processed/adam_adtte.csv", row.names = FALSE)
cat("ADTTE:", nrow(adtte), "records\n")
print(adtte %>% count(PARAMCD, is_event = CNSR == 0))
print(head(adtte, 4))
