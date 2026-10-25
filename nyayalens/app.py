"""NyayaLens dashboard (Streamlit). Reads the precomputed CSVs in data/processed."""
from pathlib import Path
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

DATA = Path(__file__).parent / "data" / "processed"
FEAT_LABELS = {"conviction_rate": "Conviction rate", "discharge_share": "Discharge share",
               "pendency_rate": "Pendency rate", "without_trial_share": "Ended without trial"}
TIER_COLORS = {"Strong": "#C00000", "Moderate": "#E8830C", "Watch": "#1D4FBF", "Typical": "#B8B8B8"}
TIER_ORDER = ["Strong", "Moderate", "Watch", "Typical"]

st.set_page_config(page_title="NyayaLens", page_icon="⚖️", layout="wide")


@st.cache_data
def load():
    res = pd.read_csv(DATA / "final_results_2023.csv")
    feats = pd.read_csv(DATA / "features_2023.csv")
    sens = pd.read_csv(DATA / "sensitivity_summary.csv")
    val = pd.read_csv(DATA / "validation_summary.csv")
    return res, feats, sens, val


res, feats, sens, val = load()
med = {f: float(np.nanmedian(res[f])) for f in FEAT_LABELS}

st.title("⚖️ NyayaLens")
st.caption("Explainable anomaly analysis of court outcomes in India's metropolitan cities, NCRB Crime in India 2023 "
           "(Tables 18B.1 IPC and 18B.3 SLL)")

tabs = st.tabs(["Overview", "Flagged heads", "Head explorer", "Methods", "Data quality", "Limitations"])

# ---------------------------------------------------------------- Overview
with tabs[0]:
    c = st.columns(5)
    c[0].metric("Crime heads parsed", len(feats))
    c[1].metric("Analysed (30+ completed trials)", len(res))
    c[2].metric("Insufficient data", int((~feats.analysis_set).sum()))
    c[3].metric("Strong flags", int((res.tier == "Strong").sum()))
    c[4].metric("Moderate flags", int((res.tier == "Moderate").sum()))
    st.markdown("Each dot is one crime head. Most heads cluster at roughly one-third conviction and "
                "about 90% pendency; flagged heads sit away from that cluster. Hover for details.")
    plot = res.assign(conviction_pct=res.conviction_rate * 100, pendency_pct=res.pendency_rate * 100)
    chart = (alt.Chart(plot).mark_circle(opacity=0.8)
             .encode(x=alt.X("conviction_pct:Q", title="Conviction rate (%)", scale=alt.Scale(domain=[0, 100])),
                     y=alt.Y("pendency_pct:Q", title="Pendency rate (%)", scale=alt.Scale(domain=[40, 100])),
                     size=alt.Size("trials_completed:Q", scale=alt.Scale(type="log", range=[40, 700]), title="Completed trials"),
                     color=alt.Color("tier:N", scale=alt.Scale(domain=TIER_ORDER, range=[TIER_COLORS[t] for t in TIER_ORDER]), title="Tier"),
                     tooltip=["crime_head", "table", "tier", alt.Tooltip("conviction_pct:Q", format=".1f"),
                              alt.Tooltip("pendency_pct:Q", format=".1f"), "trials_completed"])
             .properties(height=430))
    st.altair_chart(chart, width="stretch")
    st.info("**Tiers.** *Strong*: at least two methods flag it, the flag survives at least 80% of bootstrap re-draws, "
            "and its confidence interval clearly excludes the peer median. *Moderate*: weaker agreement or stability. "
            "*Watch*: flagged by one method only. *Typical*: not flagged.")

# ---------------------------------------------------------------- Flagged
with tabs[1]:
    f1, f2 = st.columns(2)
    tbl = f1.multiselect("Law", ["IPC", "SLL"], default=["IPC", "SLL"])
    tiers = f2.multiselect("Tier", TIER_ORDER[:3], default=["Strong", "Moderate"])
    v = res[res.table.isin(tbl) & res.tier.isin(tiers)].copy()
    v["tier"] = pd.Categorical(v.tier, TIER_ORDER, ordered=True)
    v = v.sort_values(["tier", "stab_consensus"], ascending=[True, False])
    show = pd.DataFrame({
        "Tier": v.tier.astype(str), "Law": v.table, "Code": v.sl_code, "Crime head": v.crime_head,
        "Completed trials": v.trials_completed.astype(int), "Conviction %": v.conviction_rate * 100,
        "Pendency %": v.pendency_rate * 100, "No-trial %": v.without_trial_share * 100,
        "Methods agreeing (of 3)": v.n_methods, "Stability %": v.stab_consensus * 100, "Why flagged": v.explanation})
    st.dataframe(show, width="stretch", hide_index=True, column_config={
        "Conviction %": st.column_config.NumberColumn(format="%.1f"),
        "Pendency %": st.column_config.NumberColumn(format="%.1f"),
        "No-trial %": st.column_config.NumberColumn(format="%.1f"),
        "Stability %": st.column_config.NumberColumn(format="%.0f"),
        "Why flagged": st.column_config.TextColumn(width="large")})
    st.download_button("Download this table (CSV)", show.to_csv(index=False), "nyayalens_flagged.csv", "text/csv")
    st.caption("Stability = share of 100 bootstrap re-draws in which at least two methods flagged the head.")

# ---------------------------------------------------------------- Explorer
with tabs[2]:
    names = (feats.table + " " + feats.sl_code.astype(str) + " | " + feats.crime_head).tolist()
    pick = st.selectbox("Choose a crime head", names, index=0)
    row = feats.iloc[names.index(pick)]
    if not row.analysis_set:
        st.warning(f"Insufficient data: only {int(row.trials_completed)} completed trials (minimum 30). "
                   "Rates are not reliable enough to flag.")
        st.dataframe(row[["pending_prev", "sent_for_trial", "total_for_trial", "convicted", "discharged",
                          "acquitted", "trials_completed", "pending_end"]].to_frame("count"), width="stretch")
    else:
        r = res[(res.table == row.table) & (res.sl_code.astype(str) == str(row.sl_code))].iloc[0]
        st.markdown(f"**Tier: {r.tier}**  |  methods agreeing: {int(r.n_methods)} of 3  |  bootstrap stability: {r.stab_consensus:.0%}")
        st.write(r.explanation)
        long = pd.DataFrame([{"Measure": FEAT_LABELS[f], "Value": r[f] * 100, "Low": r[f + "_lo"] * 100,
                              "High": r[f + "_hi"] * 100, "Peer median": med[f] * 100} for f in FEAT_LABELS])
        base = alt.Chart(long).encode(y=alt.Y("Measure:N", sort=None, title=None))
        layers = (base.mark_rule(size=3, color="#1D4FBF").encode(x=alt.X("Low:Q", title="% (95% confidence interval)", scale=alt.Scale(domain=[0, 100])), x2="High:Q")
                  + base.mark_circle(size=120, color="#1D4FBF").encode(x="Value:Q")
                  + base.mark_tick(color="#C00000", thickness=3, size=28).encode(x="Peer median:Q"))
        st.altair_chart(layers.properties(height=220), width="stretch")
        st.caption("Blue dot and line: this head's value and 95% Wilson interval. Red tick: median of all analysed heads.")

# ---------------------------------------------------------------- Methods
with tabs[3]:
    st.markdown("""
**Features (per crime head):** conviction rate, discharge share, pendency rate and share of cases ended without trial,
each with a Wilson 95% interval. Heads with fewer than 30 completed trials are marked *insufficient data*.

**Detection (same standardised inputs for all three):**
1. **Robust z-score** (median / MAD on logit-transformed rates) is the main method. A head is flagged if any feature has |z| ≥ 3.5.
2. **Isolation Forest** (500 trees, fixed seed) and 3. **Local Outlier Factor** are comparison methods; each flags the most isolated 10%.

**Stability:** each head's outcome counts are re-drawn 100 times from the observed proportions, and all detectors are re-run.
""")
    st.subheader("Sensitivity to the contamination setting")
    st.dataframe(sens.rename(columns={"contamination": "Contamination", "flagged_robust_z": "Robust z", "flagged_isolation_forest": "Isolation Forest",
                                      "flagged_lof": "LOF", "if_and_z": "IF ∩ z", "lof_and_z": "LOF ∩ z", "if_and_lof": "IF ∩ LOF"}),
                 width="stretch", hide_index=True)
    st.caption("The robust z-score does not depend on contamination; Isolation Forest and LOF flag a fixed share by design.")
    agree = res.n_methods.value_counts().reindex([0, 1, 2, 3], fill_value=0).rename_axis("Methods flagging").reset_index(name="Heads")
    st.subheader("Agreement between methods")
    st.dataframe(agree, hide_index=True)

# ---------------------------------------------------------------- Quality
with tabs[4]:
    st.markdown("The PDFs were parsed into one table and checked against the arithmetic printed in NCRB's own column headers.")
    st.dataframe(val.rename(columns={"check": "Check", "comparisons": "Comparisons", "failures": "Failures"}), width="stretch", hide_index=True)
    st.caption("Zero failures means every row, parent, subtotal and grand total reconciles with the published figures.")

# ---------------------------------------------------------------- Limits
with tabs[5]:
    st.markdown("""
- **Flags are statistical signals, not findings of wrongdoing.** They show that a crime head differs from its peers, not why.
- **One year and aggregated data.** This covers 2023 for 19 metropolitan cities combined; it cannot show trends or compare cities or states.
- **Case mix differs by crime head.** Petty regulatory offences (traffic, tobacco, local police acts) are processed in bulk and naturally show very high conviction; comparing them with serious IPC offences means they stand out by construction.
- **Reporting practices vary** between states and courts, and the tables are compiled from data provided by States/UTs.
- **Small heads are excluded.** 91 heads with fewer than 30 completed trials are reported as insufficient data and never flagged.
- **Model choices matter.** Thresholds (|z| ≥ 3.5, 10% contamination, 30-trial minimum) are conventional defaults, shown with a sensitivity check, not tuned to find a particular result.
""")
