from __future__ import annotations
import streamlit as st
import pandas as pd
from components.common import apply_style,settings_and_client,show_source,get_leads_or_error,lead_options,json_payload,show_backend_error,empty_state
from components.sidebar import render_sidebar
from ai.scoring import calculate_lead_score,DEFAULT_WEIGHTS

apply_style();render_sidebar();settings,client=settings_and_client()
st.title("Explainable Lead Scoring");st.caption("A configurable rule-based heuristic. This score is not a trained conversion-probability prediction.");show_source(settings)
leads=get_leads_or_error(client);opts=lead_options(leads)
if not opts:empty_state("No leads available","Create a lead or restore the backend connection first.");st.stop()
lead_id=st.selectbox("Select lead",list(opts),format_func=opts.get);lead=client.get_lead(lead_id)
st.subheader("Scoring weights")
cols=st.columns(2);weights={}
for i,(name,default) in enumerate(DEFAULT_WEIGHTS.items()): weights[name]=cols[i%2].slider(name.replace("_"," ").title(),0,30,int(default),key=f"weight_{name}")
if st.button("Calculate score",type="primary"):
    st.session_state.sg_score=calculate_lead_score(lead,weights,settings.score_threshold_qualified,settings.score_threshold_nurture);st.session_state.sg_score_lead=lead_id
score=st.session_state.get("sg_score")
if score:
    a,b=st.columns([1,3]);a.metric("Lead score",f"{score.score}/100");b.markdown(f"### {score.qualification_category}");b.write(score.recommended_next_action)
    st.caption(score.methodology_note)
    df=pd.DataFrame([x.model_dump() for x in score.factors]);st.dataframe(df[["name","weight","normalized_value","points","signal","explanation"]],use_container_width=True,hide_index=True,column_config={"normalized_value":st.column_config.NumberColumn("Factor fit",format="%.0%%")})
    c1,c2=st.columns(2)
    with c1:st.markdown("#### Positive signals");st.write(score.positive_signals or ["None"])
    with c2:st.markdown("#### Negative signals / gaps");st.write(score.negative_signals or score.missing_information or ["None"])
    if st.button("Save score through backend",type="primary"):
        try: client.save_lead_score(st.session_state.sg_score_lead,{"score":json_payload(score),"weights":weights,"method":"rule_based_heuristic"});st.success("Score was submitted to the configured backend.")
        except Exception as exc: show_backend_error(exc)
