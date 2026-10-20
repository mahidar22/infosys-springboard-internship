from __future__ import annotations
import json
import streamlit as st
from components.common import apply_style,settings_and_client,show_source,get_leads_or_error,lead_options,record_execution,json_payload,show_backend_error,empty_state
from components.sidebar import render_sidebar
from components.insight_panels import bullets
from ai.providers import create_provider,ProviderError
from ai.graph import run_workflow

apply_style();render_sidebar();settings,client=settings_and_client()
st.title("Conversation Intelligence");st.caption("Summaries extract only from the transcript and notes you provide. Long inputs are chunked before hierarchical review.");show_source(settings)
leads=get_leads_or_error(client);opts=lead_options(leads)
if not opts:empty_state("No leads available","Create a lead or restore the backend connection first.");st.stop()
lead_id=st.selectbox("Associated lead",list(opts),format_func=opts.get)
with st.form("conversation_form"):
    transcript=st.text_area("Meeting transcript",height=260,placeholder="Paste a meeting transcript. Speaker labels are helpful.")
    file=st.file_uploader("Or upload a transcript",type=["txt","md","csv"])
    notes=st.text_area("Meeting notes",height=120,placeholder="Optional notes; they are also treated as source material.")
    submitted=st.form_submit_button("Summarize conversation",type="primary")
if submitted:
    uploaded=""
    if file:
        try: uploaded=file.getvalue().decode("utf-8-sig")
        except UnicodeDecodeError: st.error("Transcript files must use UTF-8 encoding.")
    source=transcript.strip() or uploaded.strip()
    if not source and not notes.strip(): st.error("Paste a transcript, upload a supported transcript file, or enter meeting notes.")
    elif len(source)+len(notes)>settings.max_transcript_chars: st.error(f"The supplied content exceeds the configured limit of {settings.max_transcript_chars:,} characters.")
    else:
        try:
            with st.spinner("Extracting source-grounded discussion points and actions…"):
                response=run_workflow("conversation",{"transcript":source,"notes":notes},create_provider(settings))
            record_execution(response.execution);st.session_state.sg_conversation_response=response;st.session_state.sg_conversation_lead=lead_id;st.session_state.sg_conversation_version=st.session_state.get("sg_conversation_version",0)+1
        except ProviderError as exc: st.error(str(exc))
response=st.session_state.get("sg_conversation_response")
if response and response.result:
    summary=response.result;version=st.session_state.get("sg_conversation_version",0)
    st.subheader("Review summary")
    edited_summary=st.text_area("Executive summary",summary.executive_summary,height=130,key=f"conv_summary_{version}")
    bullets("Key discussion points",summary.key_discussion_points);c1,c2=st.columns(2)
    with c1:bullets("Customer requirements",summary.customer_requirements);bullets("Pain points",summary.pain_points);bullets("Objections",summary.objections);bullets("Product interests",summary.product_interests)
    with c2:bullets("Buying signals",summary.buying_signals);bullets("Competitor mentions",summary.competitor_mentions);bullets("Decisions & commitments",summary.decisions_and_commitments)
    st.markdown("#### Action items")
    if summary.action_items: st.dataframe([x.model_dump() for x in summary.action_items],use_container_width=True,hide_index=True)
    else: st.caption("No explicit action item was extracted.")
    follow=st.text_area("Suggested follow-up message",summary.suggested_follow_up,height=100,key=f"conv_follow_{version}")
    if summary.missing_or_uncertain: st.warning("Uncertain or missing: "+" · ".join(summary.missing_or_uncertain))
    st.caption(summary.source_note)
    if st.button("Save approved summary through backend",type="primary"):
        try:
            payload=json_payload(summary);payload["executive_summary"]=edited_summary;payload["suggested_follow_up"]=follow
            client.save_conversation(st.session_state.sg_conversation_lead,{"summary":payload,"execution":json_payload(response.execution)})
            st.success("Approved conversation summary was submitted to the configured backend.")
        except Exception as exc: show_backend_error(exc)
