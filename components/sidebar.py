from __future__ import annotations
import streamlit as st
from components.common import settings_and_client

def render_sidebar() -> None:
    settings, _ = settings_and_client()
    with st.sidebar:
        st.markdown("## SalesGenie AI")
        st.caption("Sales assistant & lead intelligence")
        st.divider()
        if settings.demo_mode:
            st.warning("Demo mode is active", icon="⚠️")
        else:
            st.success("Configured backend mode", icon="✓")
        st.caption(f"LLM: {settings.llm_provider} · {settings.llm_model}")
        st.caption("Use **AI Activity & Configuration** to change runtime settings. API keys remain hidden.")
        st.divider()
        st.caption("AI outputs are suggestions. Review before saving or sending.")
