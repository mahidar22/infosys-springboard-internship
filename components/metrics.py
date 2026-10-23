from __future__ import annotations
import streamlit as st

def metric_cards(analytics: dict) -> None:
    cols=st.columns(6)
    average_score=analytics.get("average_lead_score")
    values=[("Total leads",analytics.get("total_leads","—")),("Qualified",analytics.get("qualified_leads","—")),("Avg. heuristic score",average_score if average_score is not None else "—"),("Conversion rate",f"{analytics['conversion_rate']}%" if analytics.get("conversion_rate") is not None else "Not provided"),("Outreach activity",analytics.get("outreach_activity","—")),("Open follow-ups",analytics.get("follow_up_tasks","—"))]
    for col,(label,value) in zip(cols,values): col.metric(label,value)
