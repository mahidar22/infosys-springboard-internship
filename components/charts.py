from __future__ import annotations
import pandas as pd
import plotly.express as px
import streamlit as st

def dashboard_charts(analytics:dict)->None:
    c1,c2=st.columns(2)
    pipe=pd.DataFrame(analytics.get("pipeline_distribution",[])); scores=pd.DataFrame(analytics.get("lead_score_distribution",[])); activity=pd.DataFrame(analytics.get("activity_trend",[]))
    with c1:
        st.subheader("Pipeline distribution")
        if not pipe.empty: st.plotly_chart(px.funnel(pipe,x="count",y="stage",color="stage",color_discrete_sequence=px.colors.sequential.Blues_r),use_container_width=True)
        else: st.info("Pipeline distribution was not provided by the backend.")
    with c2:
        st.subheader("Lead score distribution")
        if not scores.empty: st.plotly_chart(px.bar(scores,x="band",y="count",color="band",color_discrete_sequence=px.colors.sequential.Teal),use_container_width=True)
        else: st.info("Lead-score distribution was not provided by the backend.")
    st.subheader("Sales activity trend")
    if not activity.empty: st.plotly_chart(px.line(activity,x="date",y="activity",markers=True,color_discrete_sequence=["#2563eb"]),use_container_width=True)
    else: st.info("Activity-trend data was not provided by the backend.")
