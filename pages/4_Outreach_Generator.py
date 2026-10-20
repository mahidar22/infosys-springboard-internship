from __future__ import annotations
import streamlit as st
from components.common import apply_style,settings_and_client,show_source,get_leads_or_error,lead_options,record_execution,json_payload,show_backend_error,empty_state
from components.sidebar import render_sidebar
from components.outreach_editor import draft_editor
from ai.providers import create_provider,ProviderError
from ai.graph import run_workflow

apply_style();render_sidebar();settings,client=settings_and_client()
st.title("AI Outreach Generator");st.caption("Generate editable drafts only. SalesGenie never sends a message from this workspace.");show_source(settings)
leads=get_leads_or_error(client);opts=lead_options(leads)
if not opts:empty_state("No leads available","Create a lead or restore the backend connection first.");st.stop()
lead_id=st.selectbox("Selected lead",list(opts),format_func=opts.get,key="outreach_lead")
lead=client.get_lead(lead_id)
with st.form("outreach_form"):
    a,b,c=st.columns(3)
    product=a.text_input("Product or service *",placeholder="e.g., revenue intelligence platform")
    objective=b.selectbox("Campaign objective",["Start a discovery conversation","Book a meeting","Follow up after a meeting","Re-engage an inactive prospect","Share a relevant use case"])
    channel=c.selectbox("Communication channel",["Cold email","Follow-up email","LinkedIn message","Meeting request","Sales call opening script","Short outreach message"])
    tone=a.selectbox("Tone",["Professional","Direct","Consultative","Warm"])
    length=b.selectbox("Message length",["Short","Medium","Detailed"])
    cta=c.text_input("Call to action",value="Would a 15-minute conversation next week be useful?")
    insights=st.text_area("Relevant company insights",value=lead.get("user_research", ""),placeholder="Use verified facts or approved intelligence. Do not include sensitive data.")
    submitted=st.form_submit_button("Generate draft",type="primary")

def run_draft(request:dict):
    try:
        with st.spinner("Creating a structured outreach draft…"):
            response=run_workflow("outreach",request,create_provider(settings))
        record_execution(response.execution)
        if response.errors: st.error("\n".join(response.errors));return
        st.session_state.sg_outreach_response=response;st.session_state.sg_outreach_request=request;st.session_state.sg_outreach_version=st.session_state.get("sg_outreach_version",0)+1
    except ProviderError as exc: st.error(str(exc))
if submitted:
    if not product.strip(): st.error("Product or service is required.")
    else: run_draft({"lead":lead,"product_service":product,"campaign_objective":objective,"channel":channel,"tone":tone,"message_length":length,"call_to_action":cta,"company_insights":insights,"variation_label":"primary"})
response=st.session_state.get("sg_outreach_response")
if response and response.result:
    draft=response.result
    st.subheader("Draft for review")
    subject,body=draft_editor(draft,key_prefix=f"outreach_{st.session_state.get('sg_outreach_version',0)}")
    a,b,c=st.columns(3)
    if a.button("Generate alternative",key="outreach_alternative"):
        req=dict(st.session_state.sg_outreach_request);req["variation_label"]="alternative";run_draft(req);st.rerun()
    section=b.selectbox("Section to regenerate",["Opening","Value proposition","Call to action","Subject line"],key="outreach_section")
    if c.button("Regenerate selected section",key="outreach_regen"):
        req=dict(st.session_state.sg_outreach_request);req["section_to_regenerate"]=section;req["variation_label"]=f"regenerated {section.lower()}";run_draft(req);st.rerun()
    st.caption(f"CTA: {draft.call_to_action} · Execution: {response.execution.duration_ms} ms · provider: {response.execution.provider}")
    if st.button("Save approved draft through backend",type="primary",key="save_outreach"):
        try:
            active_lead=st.session_state.sg_outreach_request["lead"]["id"]
            client.save_outreach(active_lead,{"channel":draft.channel,"subject_line":subject,"body":body,"call_to_action":draft.call_to_action,"rationale":draft.personalization_rationale,"facts_used":[x.model_dump() for x in draft.facts_used],"assumptions":draft.assumptions})
            st.success("Draft was submitted to the configured backend. It was not sent.")
        except Exception as exc: show_backend_error(exc)
