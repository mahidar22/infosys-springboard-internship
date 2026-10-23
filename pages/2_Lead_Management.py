from __future__ import annotations

import pandas as pd
import streamlit as st

from components.common import (
    apply_style,
    empty_state,
    get_leads_or_error,
    lead_options,
    settings_and_client,
    show_backend_error,
    show_source,
)
from components.lead_tables import lead_profile, lead_table
from components.sidebar import render_sidebar
from services.lead_service import save_lead
from utils.csv_import import LEAD_CSV_FIELDS, blank_lead_csv_template, preview_lead_csv, serialize_lead_csv


apply_style()
render_sidebar()
settings, client = settings_and_client()
st.title("Lead Management")
st.caption("Search, review, and submit lead updates through the configured backend API.")
show_source(settings)

leads = get_leads_or_error(client)
industries = sorted({x.get("industry", "") for x in leads if x.get("industry")})
stages = sorted({x.get("stage", "") for x in leads if x.get("stage")})
with st.expander("Search & filters", expanded=True):
    a, b, c = st.columns(3)
    query = a.text_input("Search company, contact, email, or industry")
    stage = b.selectbox("Sales stage", ["All", *stages])
    industry = c.selectbox("Industry", ["All", *industries])

filtered = get_leads_or_error(client, {"query": query, "stage": stage, "industry": industry})
lead_table(filtered)
tab_profile, tab_edit, tab_new, tab_import = st.tabs(
    ["Lead profile", "Edit lead", "Create lead", "Import CSV"]
)

with tab_profile:
    options = lead_options(filtered)
    if not options:
        empty_state("No lead selected", "Broaden the filters or import a CSV to review a lead profile.")
    else:
        selected = st.selectbox("Select lead", list(options), format_func=options.get, key="lead_profile_select")
        try:
            lead = client.get_lead(selected)
            lead_profile(lead)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### Associated outreach drafts")
                drafts = client.get_outreach(selected)
                if drafts:
                    st.dataframe(drafts, use_container_width=True, hide_index=True)
                else:
                    st.caption("No saved drafts returned by the backend.")
            with c2:
                st.markdown("#### Conversation history")
                conversations = client.get_conversations(selected)
                if conversations:
                    st.dataframe(conversations, use_container_width=True, hide_index=True)
                else:
                    st.caption("No saved summaries returned by the backend.")
        except Exception as exc:
            show_backend_error(exc)


def lead_form(prefix: str, existing: dict | None = None) -> dict:
    """Render a lead form without preselecting values for a new record."""
    existing = existing or {}
    c1, c2 = st.columns(2)
    company = c1.text_input("Company name *", existing.get("company_name", ""), key=f"{prefix}_company")
    contact = c2.text_input("Contact name", existing.get("contact_name", ""), key=f"{prefix}_contact")
    email = c1.text_input("Email", existing.get("email", ""), key=f"{prefix}_email")
    website = c2.text_input("Website", existing.get("website", ""), key=f"{prefix}_website")
    industry = c1.text_input("Industry", existing.get("industry", ""), key=f"{prefix}_industry")

    company_sizes = ["", "Unknown", "1-10", "11-50", "51-200", "201-1000", "1000+"]
    selected_size = existing.get("company_size", "")
    size_index = company_sizes.index(selected_size) if selected_size in company_sizes else 0
    company_size = c2.selectbox(
        "Company size",
        company_sizes,
        index=size_index,
        format_func=lambda value: value or "Select company size",
        key=f"{prefix}_size",
    )
    role = c1.text_input("Prospect role", existing.get("prospect_role", ""), key=f"{prefix}_role")

    statuses = ["", "New", "Active", "Inactive", "Closed"]
    selected_status = existing.get("status", "")
    status_index = statuses.index(selected_status) if selected_status in statuses else 0
    status = c2.selectbox(
        "Status",
        statuses,
        index=status_index,
        format_func=lambda value: value or "Select status",
        key=f"{prefix}_status",
    )
    sales_stages = ["", "Prospecting", "Discovery", "Qualified", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]
    selected_stage = existing.get("stage", "")
    stage_index = sales_stages.index(selected_stage) if selected_stage in sales_stages else 0
    sales_stage = c1.selectbox(
        "Sales stage",
        sales_stages,
        index=stage_index,
        format_func=lambda value: value or "Select sales stage",
        key=f"{prefix}_stage",
    )
    description = st.text_area(
        "Company description",
        existing.get("company_description", ""),
        key=f"{prefix}_description",
    )
    return {
        "company_name": company,
        "contact_name": contact,
        "email": email,
        "website": website,
        "industry": industry,
        "company_size": company_size,
        "prospect_role": role,
        "status": status,
        "stage": sales_stage,
        "company_description": description,
        "engagement_history": existing.get("engagement_history", ""),
        "explicit_needs": existing.get("explicit_needs", ""),
        "response_behavior": existing.get("response_behavior", ""),
        "user_research": existing.get("user_research", ""),
    }


with tab_edit:
    options = lead_options(leads)
    if options:
        lead_id = st.selectbox("Lead to edit", list(options), format_func=options.get, key="lead_edit_select")
        try:
            with st.form("edit_lead"):
                payload = lead_form("edit", client.get_lead(lead_id))
                submitted = st.form_submit_button("Save lead changes", type="primary")
            if submitted:
                try:
                    save_lead(client, payload, lead_id)
                    st.success("Lead update accepted by the configured backend.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        except Exception as exc:
            show_backend_error(exc)
    else:
        empty_state("No leads to edit", "Create a lead or import a CSV first.")

with tab_new:
    form_version = st.session_state.get("sg_new_lead_form_version", 0)
    with st.form(f"new_lead_{form_version}"):
        payload = lead_form(f"new_{form_version}")
        submitted = st.form_submit_button("Create lead", type="primary")
    if submitted:
        try:
            created = save_lead(client, payload)
            st.session_state["sg_new_lead_form_version"] = form_version + 1
            st.session_state["sg_new_lead_success"] = f"Lead created: {created.get('company_name')}"
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
    if st.session_state.get("sg_new_lead_success"):
        st.success(st.session_state.pop("sg_new_lead_success"))

with tab_import:
    st.caption(
        "Upload a UTF-8 CSV with a company_name column. Other supported fields are optional; "
        "blank values stay blank rather than being filled with sample data."
    )
    st.code(",".join(LEAD_CSV_FIELDS), language="text")
    st.download_button(
        "Download blank CSV template",
        blank_lead_csv_template(),
        file_name="salesgenie_leads_template.csv",
        mime="text/csv",
    )

    if st.session_state.get("sg_csv_import_message"):
        st.success(st.session_state.pop("sg_csv_import_message"))

    upload = st.file_uploader("Choose a lead CSV file", type=["csv"], key="lead_csv_upload")
    if upload is not None:
        preview = preview_lead_csv(upload.getvalue())
        if preview.warnings:
            for warning in preview.warnings:
                st.warning(warning)
        if preview.rows:
            st.caption(
                f"Preview: {len(preview.rows)} valid lead(s) from {preview.total_rows} non-empty row(s). "
                "The table shows up to 100 rows."
            )
            st.dataframe(pd.DataFrame(preview.rows[:100]), use_container_width=True, hide_index=True)
        if preview.errors:
            st.error("Fix the following CSV issues before importing:")
            for error in preview.errors:
                st.write(f"- {error}")
        elif preview.can_import:
            if preview.skipped_rows:
                st.caption(f"{preview.skipped_rows} blank row(s) will be skipped.")
            if st.button(
                f"Import {len(preview.rows)} lead(s) through backend",
                type="primary",
                key="import_leads_csv",
            ):
                try:
                    normalized_csv = serialize_lead_csv(preview.rows)
                    outcome = client.import_leads(upload.name, normalized_csv)
                    imported = int(outcome.get("imported", len(preview.rows)) or 0)
                    skipped = int(outcome.get("skipped", 0) or 0) + preview.skipped_rows
                    message = f"CSV import complete: {imported} imported; {skipped} skipped."
                    st.session_state["sg_csv_import_message"] = message
                    st.rerun()
                except Exception as exc:
                    show_backend_error(exc)
