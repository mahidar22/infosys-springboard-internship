from __future__ import annotations
import pandas as pd
import streamlit as st
from components.common import apply_style,settings_and_client,record_execution,show_backend_error
from components.sidebar import render_sidebar
from utils.config import get_settings
from ai.providers import create_provider,ProviderError
from ai.graph import run_workflow

apply_style();render_sidebar();settings,client=settings_and_client()
st.title("AI Activity & Configuration");st.caption("Runtime settings below apply only to this browser session. Secrets are read from environment variables or Streamlit secrets and are never displayed.")
with st.form("runtime_settings"):
    demo=st.toggle("Demo mode",value=settings.demo_mode,help="Uses the deterministic mock AI provider and in-memory demo backend.")
    backend=st.text_input("Backend API base URL",value=settings.backend_base_url,placeholder="https://backend.example.com")
    provider=st.selectbox("LLM provider",["mock","openai","gemini"],index=["mock","openai","gemini"].index(settings.llm_provider) if settings.llm_provider in ["mock","openai","gemini"] else 0)
    model=st.text_input("Model",value=settings.llm_model)
    a,b,c=st.columns(3);temperature=a.slider("Temperature",0.0,1.0,float(settings.llm_temperature),0.05);timeout=b.number_input("Request timeout (seconds)",1,120,int(settings.request_timeout_seconds));qualified=c.slider("Qualified threshold",50,95,int(settings.score_threshold_qualified))
    nurture=st.slider("Nurture threshold",10,qualified-1,min(int(settings.score_threshold_nurture),qualified-1))
    submitted=st.form_submit_button("Apply runtime configuration",type="primary")
if submitted:
    if not demo and not backend.strip(): st.error("A backend base URL is required outside demo mode.")
    else:
        st.session_state.salesgenie_runtime_config={"demo_mode":demo,"backend_base_url":backend.rstrip("/"),"llm_provider":provider,"llm_model":model,"llm_temperature":temperature,"request_timeout_seconds":float(timeout),"score_threshold_qualified":qualified,"score_threshold_nurture":nurture}
        st.success("Runtime configuration applied. Sensitive keys were not changed or displayed.");st.rerun()
st.divider();st.subheader("Connection diagnostics")
a,b=st.columns(2)
if a.button("Test backend connection"):
    try:
        outcome=client.health();st.success(f"Backend response: {outcome.get('status','ok')} · mode: {outcome.get('mode','configured')}")
    except Exception as exc:show_backend_error(exc)
if b.button("Run provider smoke test"):
    try:
        with st.spinner("Validating provider with a minimal structured workflow…"):
            response=run_workflow("research",{"lead":{"company_name":"Configuration test","industry":"Test","company_description":"Minimal non-customer test context."},"product_service":"test product"},create_provider(settings))
        record_execution(response.execution)
        if response.errors:st.error("\n".join(response.errors))
        else:st.success(f"Provider returned validated structured output in {response.execution.duration_ms} ms.")
    except ProviderError as exc:st.error(str(exc))
st.caption("Provider configuration state: "+("deterministic mock" if settings.demo_mode or settings.llm_provider=="mock" else f"{settings.llm_provider} (credentials are checked only when used)"))
st.divider();st.subheader("Execution activity")
log=st.session_state.get("sg_execution_log",[])
if log:
    safe=[]
    for x in log:
        safe.append({"operation":x.get("operation"),"provider":x.get("provider"),"model":x.get("model"),"duration_ms":x.get("duration_ms"),"success":x.get("success"),"used_mock":x.get("used_mock"),"errors":" | ".join(x.get("errors",[]))})
    st.dataframe(pd.DataFrame(safe),use_container_width=True,hide_index=True)
    if st.button("Clear visible activity log"):st.session_state.sg_execution_log=[];st.rerun()
else:st.info("No AI workflow execution has been recorded in this browser session.")
st.divider();st.subheader("Configuration status")
st.json({"demo_mode":settings.demo_mode,"backend_base_url":settings.backend_base_url or "Not set","backend_api_prefix":settings.backend_api_prefix,"llm_provider":settings.llm_provider,"llm_model":settings.llm_model,"request_timeout_seconds":settings.request_timeout_seconds,"credentials":"configured but hidden" if (settings.openai_api_key or settings.google_api_key) else "not detected"})
