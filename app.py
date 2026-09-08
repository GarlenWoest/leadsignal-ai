"""Streamlit 'call sheet': ranked leads with the reasoning and drafted email.

    streamlit run app.py

Scores with Claude if ANTHROPIC_API_KEY is set, otherwise the offline scorer.
"""
import os
import sys

sys.path.insert(0, "src")

import pandas as pd
import streamlit as st

from agent import qualify
from enrich import load_icp

st.set_page_config(page_title="LeadSignal AI", layout="wide")
st.title("LeadSignal AI — inbound call sheet")

mode = "Claude" if os.environ.get("ANTHROPIC_API_KEY") else "offline rule-based"
st.caption(f"Scoring with the {mode} scorer. "
           "Set ANTHROPIC_API_KEY to score with the model.")

icp = load_icp()


@st.cache_data
def score_leads():
    df = pd.read_csv("data/leads.csv")
    rows = []
    for lead in df.to_dict("records"):
        s, _ = qualify(lead, icp)
        rows.append(s.model_dump())
    return pd.DataFrame(rows)


scored = score_leads()
tiers = st.multiselect("Show tiers", ["Hot", "Warm", "Nurture", "Disqualify"],
                       default=["Hot", "Warm"])
view = scored[scored["tier"].isin(tiers)].sort_values("score", ascending=False)

left, right = st.columns([2, 1])
with left:
    st.subheader(f"{len(view)} leads")
    st.dataframe(view[["lead_id", "score", "tier", "recommended_action"]],
                 hide_index=True, use_container_width=True)
with right:
    pick = st.selectbox("Inspect a lead", view["lead_id"].tolist())
    row = view[view["lead_id"] == pick].iloc[0]
    st.metric(f"{row['lead_id']}", f"{row['score']} · {row['tier']}")
    st.write("**Why**")
    for r in row["fit_reasons"]:
        st.write(f"- {r}")
    if row["risks"]:
        st.write("**Risks**")
        for r in row["risks"]:
            st.write(f"- {r}")
    if row["draft_email"]:
        st.write("**Drafted first-touch email**")
        st.info(row["draft_email"])
