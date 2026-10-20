from __future__ import annotations
import streamlit as st
from components.common import apply_style,settings_and_client,show_source,get_leads_or_error,lead_options,record_execution,show_backend_error,empty_state
from components.sidebar import render_sidebar
from components.insight_panels import recommendation_card
from components.outreach_editor import draft_editor
from ai.providers import create_provider,ProviderError
from ai.graph import run_workflow

apply_style();render_sidebar();settings,client=settings_and_client()
st.title("Follow-up Recommendations");st.caption("Recommendations are not completed externally until an authorized system records that status.");show_source(settings)
status_filter=st.selectbox("Status",["Open","Completed","Dismissed","All"])
try: recommendations=client.get_follow_ups({"status":status_filter})
except Exception as exc:show_backend_error(exc);recommendations=[]

def status_update(rec:dict,status:str):
    try: client.update_follow_up(rec["id"],{"status":status});st.success(f"Recommendation status updated to {status} through the backend.");st.rerun()
    except Exception as exc: show_backend_error(exc)

def draft_from_rec(rec:dict):
    try:
        lead=client.get_lead(rec["lead_id"])
        with st.spinner("Generating a reviewable follow-up draft…"):
            response=run_workflow("outreach",{"lead":lead,"product_service":"your offering","campaign_objective":rec["recommended_action"],"channel":"Follow-up email","tone":"Professional","message_length":"Short","call_to_action":"Would a brief next-step conversation be helpful?","company_insights":"","variation_label":"follow-up"},create_provider(settings))
        record_execution(response.execution)
        if response.errors:st.error("\n".join(response.errors))
        else: st.session_state.sg_followup_draft=response
    except (ProviderError,Exception) as exc: st.error(str(exc))

if recommendations:
    for rec in recommendations: recommendation_card(rec,lambda r:status_update(r,"Completed"),lambda r:status_update(r,"Dismissed"),draft_from_rec)
else: empty_state("No recommendations", "No follow-up tasks were returned for this status filter.")
if st.session_state.get("sg_followup_draft"):
    response=st.session_state.sg_followup_draft
    if response.result:
        st.subheader("Generated follow-up draft — review before use")
        draft_editor(response.result,key_prefix="followup_draft")
        st.caption("This draft has not been sent or saved automatically.")
st.divider();st.subheader("Request a new recommendation")
leads=get_leads_or_error(client);opts=lead_options(leads)
if opts:
    lead_id=st.selectbox("Lead for a new recommendation",list(opts),format_func=opts.get,key="new_recommendation_lead")
    if st.button("Generate recommendation",type="secondary"):
        try:
            with st.spinner("Evaluating available lead evidence…"):
                response=run_workflow("follow_up",{"lead":client.get_lead(lead_id)},create_provider(settings))
            record_execution(response.execution);st.session_state.sg_new_recommendation=response
        except ProviderError as exc:st.error(str(exc))
    generated=st.session_state.get("sg_new_recommendation")
    if generated:
        if generated.errors:st.error("\n".join(generated.errors))
        elif generated.result:
            rec=generated.result
            with st.container(border=True):
                st.markdown(f"**{rec.related_lead}** · {rec.priority} priority")
                st.write(rec.recommended_action);st.caption(rec.reason)
                st.write("Evidence: "+("; ".join(x.statement for x in rec.supporting_evidence) or "No supporting evidence was supplied."))
                st.caption("This is a newly generated, unsaved recommendation. The configured backend contract currently only persists task status updates.")
