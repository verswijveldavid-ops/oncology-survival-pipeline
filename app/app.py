"""
app.py -- Breast Cancer Survival dashboard (Streamlit).
A guided, top-to-bottom story. Run from the project root:
    streamlit run app/app.py
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from lifelines import KaplanMeierFitter
from lifelines.statistics import multivariate_logrank_test

st.set_page_config(page_title="Breast Cancer Survival - TCGA-BRCA", layout="wide")

@st.cache_data
def load():
    return (pd.read_csv(Path("data/processed/patients_analysis.csv")),
            pd.read_csv(Path("reports/survival_rates.csv")),
            pd.read_csv(Path("reports/table1_cohort.csv")))

df, rates, table1 = load()
rate = dict(zip(rates["Group"], rates["Alive at 5 yrs (%)"]))

# --- Title + the question ----------------------------------------------
st.title("Breast Cancer Survival")
st.markdown("#### Who lives longer after a breast cancer diagnosis, and why?")
st.caption("Real, anonymous data on ~1,100 patients from the public NCI cancer "
           "database (TCGA-BRCA). Educational portfolio project.")
st.divider()

# --- 1. The patients ----------------------------------------------------
st.header("1. The patients")
st.write("We studied real people diagnosed with breast cancer. Here is who they are.")
c1, c2, c3 = st.columns(3)
c1.metric("Patients", f"{len(df):,}")
c2.metric("Died during follow-up", int((df['vital_status'] == 'Dead').sum()))
c3.metric("Typical follow-up", f"{df['os_years'].median():.1f} years")
with st.expander("See the full breakdown (age, stage, cancer type, treatment)"):
    st.dataframe(table1, hide_index=True, use_container_width=True)

# --- 2. Headline: 5-year survival --------------------------------------
st.header("2. The headline: 5-year survival")
st.write("A simple way to read survival: **out of 100 patients, how many are "
         "still alive after 5 years?**")
h = st.columns(4)
h[0].metric("All patients", f"{rate.get('All patients', '-')}%")
h[1].metric("Stage I (earliest)", f"{rate.get('Stage I', '-')}%")
h[2].metric("Stage IV (most advanced)", f"{rate.get('Stage IV', '-')}%")
h[3].metric("Triple Negative type", f"{rate.get('Triple Negative', '-')}%")
st.write("The earlier the cancer is caught, the more people are alive 5 years "
         "later. Stage I: about 90 out of 100. Stage IV: about 27 out of 100.")
with st.expander("Full 5- and 10-year survival table"):
    st.dataframe(rates, hide_index=True, use_container_width=True)

# --- 3. Explore the curves ---------------------------------------------
st.header("3. Explore the survival curves")
st.write("A survival curve shows the share of a group still alive as years pass. "
         "It starts at 100% and steps down. Pick how to split the patients:")
options = {"Cancer stage": "stage_group", "Cancer type": "molecular_subtype",
           "ER status": "er_status_by_ihc"}
choice = st.selectbox("Split patients by:", list(options.keys()))
col = options[choice]
d = df[df[col].notna() & (df[col] != "Unknown")]
keep = d[col].value_counts()
keep = keep[keep >= 10].index.tolist()
d = d[d[col].isin(keep)]
fig, ax = plt.subplots(figsize=(8, 5))
kmf = KaplanMeierFitter()
for level in keep:
    g = d[d[col] == level]
    kmf.fit(g["os_years"], g["os_event"], label=f"{level} (n={len(g)})")
    kmf.plot_survival_function(ax=ax, ci_show=False)
ax.set_xlabel("Years after diagnosis"); ax.set_ylabel("Share still alive"); ax.set_ylim(0, 1)
st.pyplot(fig)
if len(keep) >= 2:
    p = multivariate_logrank_test(d["os_years"], d[col], d["os_event"]).p_value
    if p < 0.05:
        st.success(f"The gap between these groups is real, not chance (p = {p:.3g}).")
    else:
        st.info(f"The gap between these groups could be chance (p = {p:.3g}).")

# --- 4. What matters most ----------------------------------------------
st.header("4. What matters most")
st.write("One chart can mislead, because things are tangled together. So we used "
         "a method that weighs everything at once. The result:")
st.markdown(
    "- **How far the cancer has spread (stage) matters most.** Stage IV raises the "
    "risk of dying about 7 times compared with Stage I.\n"
    "- **Age matters.** Older patients are at higher risk.\n"
    "- **Cancer type mattered less than it first looked**, once stage and age were "
    "taken into account.")
st.image("reports/figures/table1_mortality.png",
         caption="Share of each group who died. Higher stage means more deaths.")

# --- 5. Making the data trustworthy ------------------------------------
st.header("5. How we made the data trustworthy")
st.write("Our first version used only one file to decide who lived or died. It was "
         "incomplete. When we combined every follow-up file, we found:")
st.markdown(
    "- **48 patients we had marked \"alive\" had actually died** (recorded only in "
    "another file).\n"
    "- Follow-up time roughly **doubled** once all records were included.")
st.write("Fixing this changed the results. Catching and correcting it is a core part "
         "of careful data work.")
b = st.columns(2)
b[0].metric("Deaths counted - before fix", "104")
b[1].metric("Deaths counted - after fix", "152", delta="+48")

# --- 6. Honest limits ---------------------------------------------------
st.header("6. Honest limits")
st.markdown(
    "- The far end of each curve rests on very few patients, so it is less reliable.\n"
    "- Cancer type is missing for some patients.\n"
    "- We did not compare treatments head-to-head, because sicker patients get "
    "different treatment - that would mislead.\n"
    "- This is real archived data, not a live clinical trial.")

st.divider()
st.caption("Built with Python (pandas, lifelines) and R (survival, admiral). Data "
           "standardised into CDISC SDTM and ADaM formats.")
