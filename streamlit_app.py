import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="HIV Care & Treatment Outcomes", page_icon="🩺", layout="wide")

# ---------- Data loading ----------
@st.cache_data
def load_data():
    df = pd.read_csv("data/HIV_Analysis_Ready.csv")
    df["date_art_started"] = pd.to_datetime(df["date_art_started"], errors="coerce")
    df["art_start_year"] = df["date_art_started"].dt.year
    stage_order = ["I", "II", "III", "IV"]
    df["clinical_stage_at_start"] = pd.Categorical(
        df["clinical_stage_at_start"], categories=stage_order, ordered=True
    )
    adherence_order = ["Poor", "Fair", "Good"]
    df["arv_adherence_latest"] = pd.Categorical(
        df["arv_adherence_latest"], categories=adherence_order, ordered=True
    )
    age_bins = [17, 24, 34, 44, 54, 61]
    age_labels = ["18-24", "25-34", "35-44", "45-54", "55-60"]
    df["age_group"] = pd.cut(df["age"], bins=age_bins, labels=age_labels)
    return df

df = load_data()

PRIMARY = "#0E7C7B"
ACCENT = "#D64550"
NEUTRAL = "#6C757D"
PALETTE = ["#0E7C7B", "#D64550", "#F2A541", "#3B6EA5", "#8E44AD"]

# ---------- Sidebar filters ----------
st.sidebar.title("🩺 Filters")
st.sidebar.caption("Filter the cohort — every chart below updates.")

sex_sel = st.sidebar.multiselect("Sex", sorted(df["sex"].dropna().unique()), default=list(df["sex"].dropna().unique()))
age_range = st.sidebar.slider("Age range", int(df["age"].min()), int(df["age"].max()), (int(df["age"].min()), int(df["age"].max())))
stage_sel = st.sidebar.multiselect("Clinical stage at start", ["I", "II", "III", "IV"], default=["I", "II", "III", "IV"])
facility_sel = st.sidebar.multiselect("Facility level", sorted(df["facility_level"].dropna().unique()), default=list(df["facility_level"].dropna().unique()))
adherence_sel = st.sidebar.multiselect("Adherence", ["Good", "Fair", "Poor"], default=["Good", "Fair", "Poor"])

fdf = df[
    df["sex"].isin(sex_sel)
    & df["age"].between(age_range[0], age_range[1])
    & (df["clinical_stage_at_start"].isin(stage_sel) | df["clinical_stage_at_start"].isna())
    & df["facility_level"].isin(facility_sel)
    & (df["arv_adherence_latest"].isin(adherence_sel) | df["arv_adherence_latest"].isna())
]

st.sidebar.markdown("---")
st.sidebar.metric("Patients in view", f"{len(fdf):,}", delta=f"of {len(df):,} total", delta_color="off")

# ---------- Header ----------
st.title("HIV Care & Treatment Outcomes Dashboard")
st.caption(
    f"Cohort of adults aged 18–60 on ART · {df['date_art_started'].min().date()} to "
    f"{df['date_art_started'].max().date()} · {len(df):,} patient records"
)

# ---------- KPI row ----------
k1, k2, k3, k4, k5 = st.columns(5)
mortality = fdf["outcome_dead"].mean() * 100 if len(fdf) else 0
vl_supp = fdf["vl_suppressed"].mean() * 100 if len(fdf) else 0
good_adh = (fdf["arv_adherence_latest"] == "Good").mean() * 100 if len(fdf) else 0
interrupt = fdf["art_interrupted"].mean() * 100 if len(fdf) else 0
med_cd4 = fdf["cd4_at_start"].median() if len(fdf) else 0

k1.metric("Patients", f"{len(fdf):,}")
k2.metric("Mortality rate", f"{mortality:.2f}%")
k3.metric("Viral load suppressed", f"{vl_supp:.1f}%", help="Among patients with a viral load test on record")
k4.metric("Good adherence", f"{good_adh:.1f}%")
k5.metric("Median CD4 at start", f"{med_cd4:.0f}" if pd.notna(med_cd4) else "n/a")

st.markdown("---")

# ---------- Key insights ----------
st.subheader("Key Insights")
insights = [
    "**Overall mortality is low (0.85%)** across the cohort, but it rises sharply with clinical severity: "
    "**0.6% at Stage I vs. 2.8% at Stage IV**.",
    "**Adherence is the strongest modifiable risk factor.** Patients with 'Poor' adherence die at "
    "a higher rate of those with 'Good' adherence.",
    "**Viral suppression essentially eliminates mortality risk** in this data: suppressed patients have a "
    "0.07% death rate vs. 1.5% for unsuppressed.",
    "**ART interruption is strongly associated with death**: interrupted patients die at **6.7x** the rate "
    "of those with continuous treatment (3.9% vs 0.6%).",
    "**Women make up 70% of the cohort** but have a lower mortality rate than men (0.72% vs 1.16%), "
    "consistent with men presenting later or engaging less with care.",
]
for i in insights:
    st.markdown(f"- {i}")

st.markdown("---")

# ---------- Tabs ----------
tab1, tab2, tab3, tab4 = st.tabs(["📊 Demographics", "⚠️ Mortality Drivers", "💊 Treatment & Adherence", "🏥 Facilities & Trends"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Age distribution")
        fig = px.histogram(fdf, x="age", nbins=30, color_discrete_sequence=[PRIMARY])
        fig.update_layout(xaxis_title="Age", yaxis_title="Patients", bargap=0.05)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("#### Sex distribution")
        sex_counts = fdf["sex"].value_counts().reset_index()
        sex_counts.columns = ["sex", "count"]
        fig = px.pie(sex_counts, names="sex", values="count", color_discrete_sequence=PALETTE, hole=0.45)
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("#### Clinical stage at ART start")
        stage_counts = fdf["clinical_stage_at_start"].value_counts().sort_index().reset_index()
        stage_counts.columns = ["stage", "count"]
        fig = px.bar(stage_counts, x="stage", y="count", color_discrete_sequence=[PRIMARY])
        fig.update_layout(xaxis_title="Clinical stage", yaxis_title="Patients")
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        st.markdown("#### Weight at start (kg) by sex")
        fig = px.box(fdf, x="sex", y="weight_at_start_kg", color="sex", color_discrete_sequence=PALETTE)
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Weight (kg)")
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("#### Mortality rate by clinical stage")
    stage_mort = fdf.groupby("clinical_stage_at_start", observed=True)["outcome_dead"].mean().mul(100).reset_index()
    fig = px.bar(stage_mort, x="clinical_stage_at_start", y="outcome_dead", color_discrete_sequence=[ACCENT], text_auto=".2f")
    fig.update_layout(xaxis_title="Clinical stage", yaxis_title="Mortality rate (%)")
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Mortality by viral load suppression")
        vl_mort = fdf.groupby("vl_suppressed")["outcome_dead"].mean().mul(100).reset_index()
        vl_mort["vl_suppressed"] = vl_mort["vl_suppressed"].map({0: "Not suppressed", 1: "Suppressed"})
        fig = px.bar(vl_mort, x="vl_suppressed", y="outcome_dead", color_discrete_sequence=[ACCENT], text_auto=".2f")
        fig.update_layout(xaxis_title="", yaxis_title="Mortality rate (%)")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("#### Mortality by ART interruption")
        int_mort = fdf.groupby("art_interruption")["outcome_dead"].mean().mul(100).reset_index()
        fig = px.bar(int_mort, x="art_interruption", y="outcome_dead", color_discrete_sequence=[ACCENT], text_auto=".2f")
        fig.update_layout(xaxis_title="Interrupted ART?", yaxis_title="Mortality rate (%)")
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("#### Mortality by sex")
        sex_mort = fdf.groupby("sex")["outcome_dead"].mean().mul(100).reset_index()
        fig = px.bar(sex_mort, x="sex", y="outcome_dead", color_discrete_sequence=[ACCENT], text_auto=".2f")
        fig.update_layout(xaxis_title="", yaxis_title="Mortality rate (%)")
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        st.markdown("#### Mortality by age group")
        age_mort = fdf.groupby("age_group", observed=True)["outcome_dead"].mean().mul(100).reset_index()
        fig = px.bar(age_mort, x="age_group", y="outcome_dead", color_discrete_sequence=[ACCENT], text_auto=".2f")
        fig.update_layout(xaxis_title="Age group", yaxis_title="Mortality rate (%)")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### CD4 count at start: survivors vs. deceased")
    fig = px.box(fdf.dropna(subset=["cd4_at_start"]), x="outcome_dead", y="cd4_at_start", color="outcome_dead",
                 color_discrete_sequence=PALETTE)
    fig.update_layout(xaxis=dict(tickmode="array", tickvals=[0, 1], ticktext=["Survived", "Deceased"]),
                       xaxis_title="", yaxis_title="CD4 count at start", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Adherence distribution")
        adh_counts = fdf["arv_adherence_latest"].value_counts().reindex(["Poor", "Fair", "Good"]).reset_index()
        adh_counts.columns = ["adherence", "count"]
        fig = px.bar(adh_counts, x="adherence", y="count", color="adherence",
                     color_discrete_map={"Good": PRIMARY, "Fair": "#F2A541", "Poor": ACCENT})
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Patients")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("#### Mortality rate by adherence level")
        adh_mort = fdf.groupby("arv_adherence_latest", observed=True)["outcome_dead"].mean().mul(100).reset_index()
        fig = px.bar(adh_mort, x="arv_adherence_latest", y="outcome_dead", color="arv_adherence_latest",
                     color_discrete_map={"Good": PRIMARY, "Fair": "#F2A541", "Poor": ACCENT}, text_auto=".2f")
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Mortality rate (%)")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Viral load suppression by adherence level")
    vl_by_adh = fdf.groupby("arv_adherence_latest", observed=True)["vl_suppressed"].mean().mul(100).reset_index()
    fig = px.bar(vl_by_adh, x="arv_adherence_latest", y="vl_suppressed", color_discrete_sequence=[PRIMARY], text_auto=".1f")
    fig.update_layout(xaxis_title="Adherence", yaxis_title="Viral load suppressed (%)")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### ART interruption rate by clinical stage")
    int_by_stage = fdf.groupby("clinical_stage_at_start", observed=True)["art_interrupted"].mean().mul(100).reset_index()
    fig = px.bar(int_by_stage, x="clinical_stage_at_start", y="art_interrupted", color_discrete_sequence=[NEUTRAL], text_auto=".1f")
    fig.update_layout(xaxis_title="Clinical stage", yaxis_title="Interruption rate (%)")
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Patients by facility level")
        fac_counts = fdf["facility_level"].value_counts().reset_index()
        fac_counts.columns = ["facility_level", "count"]
        fig = px.bar(fac_counts, x="facility_level", y="count", color_discrete_sequence=[PRIMARY])
        fig.update_layout(xaxis_title="", yaxis_title="Patients")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("#### Patients by facility type")
        fac_type = fdf["facility_type"].value_counts().reset_index()
        fac_type.columns = ["facility_type", "count"]
        fig = px.pie(fac_type, names="facility_type", values="count", color_discrete_sequence=PALETTE, hole=0.45)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Mortality rate by facility level")
    fac_mort = fdf.groupby("facility_level")["outcome_dead"].mean().mul(100).reset_index()
    fig = px.bar(fac_mort, x="facility_level", y="outcome_dead", color_discrete_sequence=[ACCENT], text_auto=".2f")
    fig.update_layout(xaxis_title="", yaxis_title="Mortality rate (%)")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### ART enrollment trend over time")
    yearly = fdf.dropna(subset=["art_start_year"]).groupby("art_start_year").size().reset_index(name="new_patients")
    yearly["art_start_year"] = yearly["art_start_year"].astype(int)
    fig = px.line(yearly, x="art_start_year", y="new_patients", markers=True, color_discrete_sequence=[PRIMARY])
    fig.update_layout(xaxis_title="Year ART started", yaxis_title="New patients enrolled")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
with st.expander("🔍 View filtered raw data"):
    st.dataframe(fdf, use_container_width=True)
    st.download_button("Download filtered data as CSV", fdf.to_csv(index=False), "filtered_HIV_Analysis_Ready.csv", "text/csv")
