from __future__ import annotations
import pandas as pd
import streamlit as st
from components.common import settings_and_client, show_source, show_backend_error, record_execution, empty_state
from components.metrics import metric_cards
from components.charts import dashboard_charts
from ai.providers import create_provider, ProviderError
from ai.graph import run_workflow

def render_dashboard() -> None:
    settings, client=settings_and_client()
    st.title("Sales Overview")
    st.caption("Pipeline visibility from the configured backend; AI observations stay evidence-bound.")
    show_source(settings)
    try:
        leads=client.list_leads()
    except Exception as exc:
        show_backend_error(exc); return
    industries=sorted({str(x.get("industry")) for x in leads if x.get("industry")})
    with st.expander("Filters",expanded=False):
        industry=st.selectbox("Industry",["All",*industries],key="dash_industry")
    try: analytics=client.get_analytics({"industry":industry})
    except Exception as exc: show_backend_error(exc); return
    if analytics.get("is_demo"): st.caption(f"Source: {analytics.get('source')}")
    metric_cards(analytics); st.divider(); dashboard_charts(analytics)
    st.subheader("Lead pipeline")
    if leads:
        df=pd.DataFrame(leads)
        st.dataframe(df[[c for c in ["company_name","contact_name","industry","stage","status"] if c in df.columns]],use_container_width=True,hide_index=True)
    else: empty_state("No lead data", "The backend returned no leads for the selected filters.")
    st.divider(); st.subheader("AI sales insights")
    if st.button("Interpret supplied analytics",type="secondary",key="dashboard_insights"):
        try:
            with st.spinner("Interpreting supplied aggregate data…"):
                response=run_workflow("sales_insights",{"analytics":analytics},create_provider(settings))
            record_execution(response.execution); st.session_state.sg_sales_insights=response
        except ProviderError as exc: st.error(str(exc))
    response=st.session_state.get("sg_sales_insights")
    if response:
        if response.errors: st.error(" · ".join(response.errors))
        elif response.result:
            for item in response.result.insights:
                with st.container(border=True): st.markdown(f"**{item.title}**");st.write(item.observation);st.caption(f"Evidence: {item.evidence} · {item.confidence} confidence")
            st.caption(response.result.caveat)
