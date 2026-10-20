from __future__ import annotations
import streamlit as st
from components.common import apply_style,settings_and_client,show_source,get_leads_or_error,lead_options,record_execution,json_payload,show_backend_error,empty_state
from components.sidebar import render_sidebar
from components.insight_panels import research_panel
from ai.providers import create_provider,ProviderError
from ai.graph import run_workflow

apply_style();render_sidebar();settings,client=settings_and_client()
st.title("AI Lead Intelligence");st.caption("Evidence-aware analysis using the selected lead plus context you supply. It does not browse company websites unless a retrieval integration is configured.");show_source(settings)
leads=get_leads_or_error(client)
opts=lead_options(leads)
if not opts: empty_state("No leads available", "Create a lead or restore the backend connection before running intelligence.");st.stop()
lead_id=st.selectbox("Selected lead",list(opts),format_func=opts.get)
lead=client.get_lead(lead_id)
with st.form("intelligence_form"):
    a,b=st.columns(2)
    company=a.text_input("Company name",lead.get("company_name",""));website=b.text_input("Website",lead.get("website", ""))
    industry=a.text_input("Industry",lead.get("industry", ""));size=b.selectbox("Company size",["Unknown","1-10","11-50","51-200","201-1000","1000+"],index=["Unknown","1-10","11-50","51-200","201-1000","1000+"].index(lead.get("company_size","Unknown") if lead.get("company_size") in ["Unknown","1-10","11-50","51-200","201-1000","1000+"] else "Unknown"))
    description=st.text_area("Company description",lead.get("company_description", ""));role=a.text_input("Prospect role",lead.get("prospect_role", ""));product=b.text_input("Product or service being sold",placeholder="e.g., Sales analytics platform")
    research=st.text_area("User-provided research",lead.get("user_research", ""),placeholder="Paste verified research or internal notes. It is treated as untrusted reference material.")
    needs=st.text_area("Known customer needs",lead.get("explicit_needs", ""));engagement=st.text_area("Existing engagement context",lead.get("engagement_history", ""))
    submitted=st.form_submit_button("Run lead intelligence",type="primary")
if submitted:
    if not company.strip() or not product.strip(): st.error("Company name and product or service are required.")
    else:
        request={"lead":{**lead,"company_name":company,"website":website,"industry":industry,"company_size":size,"company_description":description,"prospect_role":role,"user_research":research,"explicit_needs":needs,"engagement_history":engagement},"product_service":product}
        try:
            with st.spinner("Running the lead research and qualification workflow…"):
                response=run_workflow("lead_intelligence",request,create_provider(settings))
            record_execution(response.execution);st.session_state.sg_intelligence_response=response;st.session_state.sg_intelligence_lead_id=lead_id
        except ProviderError as exc: st.error(str(exc))
response=st.session_state.get("sg_intelligence_response")
if response:
    if response.errors: st.error("\n".join(response.errors))
    elif response.research:
        research_panel(response.research,response.qualification)
        st.caption(f"Execution: {response.execution.duration_ms} ms · provider: {response.execution.provider} · {'mock' if response.execution.used_mock else 'configured provider'}")
        if st.button("Save approved intelligence through backend",type="primary"):
            saved_for=st.session_state.get("sg_intelligence_lead_id")
            try:
                client.save_company_insights(saved_for,{"research":json_payload(response.research),"qualification":json_payload(response.qualification) if response.qualification else None,"execution":json_payload(response.execution)})
                st.success("Approved intelligence was submitted to the configured backend.")
            except Exception as exc: show_backend_error(exc)
