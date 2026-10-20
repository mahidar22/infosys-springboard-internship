from __future__ import annotations
import streamlit as st
from components.common import apply_style, settings_and_client, show_source, show_backend_error, get_leads_or_error, lead_options, empty_state
from components.sidebar import render_sidebar
from components.lead_tables import lead_table, lead_profile
from services.lead_service import save_lead

apply_style();render_sidebar();settings,client=settings_and_client()
st.title("Lead Management");st.caption("Search, review, and submit lead updates through the configured backend API.");show_source(settings)
leads=get_leads_or_error(client)
industries=sorted({x.get("industry","") for x in leads if x.get("industry")}); stages=sorted({x.get("stage","") for x in leads if x.get("stage")})
with st.expander("Search & filters",expanded=True):
    a,b,c=st.columns(3);query=a.text_input("Search company, contact, email, or industry");stage=b.selectbox("Sales stage",["All",*stages]);industry=c.selectbox("Industry",["All",*industries])
filtered=get_leads_or_error(client,{"query":query,"stage":stage,"industry":industry})
lead_table(filtered)
tab_profile,tab_edit,tab_new,tab_import=st.tabs(["Lead profile","Edit lead","Create lead","Import CSV"])
with tab_profile:
    options=lead_options(filtered)
    if not options: empty_state("No lead selected", "Broaden the filters to review a lead profile.")
    else:
        selected=st.selectbox("Select lead",list(options),format_func=options.get,key="lead_profile_select")
        try:
            lead=client.get_lead(selected);lead_profile(lead)
            c1,c2=st.columns(2)
            with c1:
                st.markdown("#### Associated outreach drafts")
                drafts=client.get_outreach(selected)
                if drafts: st.dataframe(drafts,use_container_width=True,hide_index=True)
                else: st.caption("No saved drafts returned by the backend.")
            with c2:
                st.markdown("#### Conversation history")
                conv=client.get_conversations(selected)
                if conv: st.dataframe(conv,use_container_width=True,hide_index=True)
                else: st.caption("No saved summaries returned by the backend.")
        except Exception as exc: show_backend_error(exc)

def lead_form(prefix:str,existing:dict|None=None):
    existing=existing or {}
    c1,c2=st.columns(2)
    company=c1.text_input("Company name *",existing.get("company_name",""),key=f"{prefix}_company")
    contact=c2.text_input("Contact name",existing.get("contact_name",""),key=f"{prefix}_contact")
    email=c1.text_input("Email",existing.get("email",""),key=f"{prefix}_email")
    website=c2.text_input("Website",existing.get("website",""),key=f"{prefix}_website")
    industry=c1.text_input("Industry",existing.get("industry",""),key=f"{prefix}_industry")
    company_size=c2.selectbox("Company size",["Unknown","1-10","11-50","51-200","201-1000","1000+"],index=["Unknown","1-10","11-50","51-200","201-1000","1000+"].index(existing.get("company_size","Unknown") if existing.get("company_size") in ["Unknown","1-10","11-50","51-200","201-1000","1000+"] else "Unknown"),key=f"{prefix}_size")
    role=c1.text_input("Prospect role",existing.get("prospect_role",""),key=f"{prefix}_role")
    status=c2.selectbox("Status",["New","Active","Inactive","Closed"],index=max(0,["New","Active","Inactive","Closed"].index(existing.get("status","New")) if existing.get("status","New") in ["New","Active","Inactive","Closed"] else 0),key=f"{prefix}_status")
    stage=c1.selectbox("Sales stage",["Prospecting","Discovery","Qualified","Proposal","Negotiation","Closed Won","Closed Lost"],index=max(0,["Prospecting","Discovery","Qualified","Proposal","Negotiation","Closed Won","Closed Lost"].index(existing.get("stage","Prospecting")) if existing.get("stage","Prospecting") in ["Prospecting","Discovery","Qualified","Proposal","Negotiation","Closed Won","Closed Lost"] else 0),key=f"{prefix}_stage")
    description=st.text_area("Company description",existing.get("company_description",""),key=f"{prefix}_description")
    return {"company_name":company,"contact_name":contact,"email":email,"website":website,"industry":industry,"company_size":company_size,"prospect_role":role,"status":status,"stage":stage,"company_description":description,"engagement_history":existing.get("engagement_history",""),"explicit_needs":existing.get("explicit_needs",""),"response_behavior":existing.get("response_behavior",""),"user_research":existing.get("user_research","")}
with tab_edit:
    opts=lead_options(leads)
    if opts:
        id_=st.selectbox("Lead to edit",list(opts),format_func=opts.get,key="lead_edit_select")
        try:
            with st.form("edit_lead"):
                payload=lead_form("edit",client.get_lead(id_))
                submitted=st.form_submit_button("Save lead changes",type="primary")
            if submitted:
                try: save_lead(client,payload,id_);st.success("Lead update accepted by the configured backend.");st.rerun()
                except Exception as exc: st.error(str(exc))
        except Exception as exc: show_backend_error(exc)
with tab_new:
    with st.form("new_lead"):
        payload=lead_form("new")
        submitted=st.form_submit_button("Create lead",type="primary")
    if submitted:
        try: created=save_lead(client,payload);st.success(f"Lead created: {created.get('company_name')}");st.rerun()
        except Exception as exc: st.error(str(exc))
with tab_import:
    st.caption("CSV headers accepted by the documented adapter: company_name, contact_name, email, website, industry, company_size, prospect_role, status, stage, company_description.")
    st.download_button("Download CSV template","company_name,contact_name,email,industry,company_size,prospect_role,status,stage\nExample Company,Ada Example,ada@example.com,Technology,51-200,Head of Sales,New,Prospecting\n",file_name="salesgenie_leads_template.csv",mime="text/csv")
    upload=st.file_uploader("CSV file",type=["csv"])
    if upload and st.button("Import through backend",type="primary"):
        try:
            outcome=client.import_leads(upload.name,upload.getvalue());st.success(f"Backend import result: {outcome.get('imported',0)} imported; {outcome.get('skipped',0)} skipped.");st.rerun()
        except Exception as exc: show_backend_error(exc)
