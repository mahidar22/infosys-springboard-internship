from __future__ import annotations
import json
from typing import Any
import streamlit as st
from services.api_client import APIClient, BackendAPIError
from utils.config import runtime_settings


def apply_style() -> None:
    st.markdown("""<style>
    .block-container{max-width:1450px;padding-top:1.6rem;padding-bottom:3rem}
    [data-testid="stMetric"]{background:#fff;border:1px solid #e6eaf0;border-radius:14px;padding:14px 16px;box-shadow:0 2px 6px rgba(15,23,42,.04)}
    .sg-label{font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;color:#64748b;font-weight:700}
    .sg-panel{border:1px solid #e5e7eb;border-radius:12px;padding:1rem 1.1rem;background:#fff;margin:.5rem 0}
    .sg-demo{background:#fffbeb;color:#854d0e;border:1px solid #fde68a;border-radius:10px;padding:.65rem .8rem;margin:.35rem 0 1rem}
    .sg-fact{border-left:4px solid #16a34a;background:#f0fdf4;padding:.5rem .65rem;margin:.3rem 0;border-radius:4px}
    .sg-hypothesis{border-left:4px solid #d97706;background:#fffbeb;padding:.5rem .65rem;margin:.3rem 0;border-radius:4px}
    </style>""", unsafe_allow_html=True)


def settings_and_client() -> tuple[Any, APIClient]:
    settings = runtime_settings()
    signature=(settings.demo_mode,settings.backend_base_url,settings.backend_api_prefix,settings.backend_token,settings.request_timeout_seconds)
    if st.session_state.get("sg_client_signature") != signature:
        old=st.session_state.get("sg_api_client")
        if old:
            try: old.close()
            except Exception: pass
        st.session_state.sg_api_client=APIClient(settings)
        st.session_state.sg_client_signature=signature
    return settings, st.session_state.sg_api_client


def show_source(settings: Any, context: str = "") -> None:
    if settings.demo_mode:
        st.markdown(f'<div class="sg-demo"><b>Demo mode</b> — {context or "Results use deterministic mock AI and in-memory demo backend data. They are not live business data or external research."}</div>', unsafe_allow_html=True)


def show_backend_error(exc: Exception) -> None:
    st.error(f"Backend request failed: {exc}")
    st.caption("Check the API base URL, prefix, credentials, endpoint contract, and backend availability in AI Activity & Configuration.")


def get_leads_or_error(client: APIClient, filters: dict[str,Any]|None=None) -> list[dict[str,Any]]:
    try: return client.list_leads(filters)
    except Exception as exc: show_backend_error(exc); return []


def lead_options(leads: list[dict[str,Any]]) -> dict[str,str]:
    return {str(x["id"]): f"{x.get('company_name','Unknown')} — {x.get('contact_name') or 'No contact'}" for x in leads}


def record_execution(execution: Any) -> None:
    rows=st.session_state.setdefault("sg_execution_log", [])
    row=execution.model_dump() if hasattr(execution,"model_dump") else dict(execution)
    rows.insert(0,row); del rows[25:]


def json_payload(model: Any) -> dict[str, Any]:
    if hasattr(model,"model_dump"): return model.model_dump(mode="json")
    return json.loads(json.dumps(model, default=str))


def empty_state(title: str, body: str) -> None:
    st.info(f"**{title}**\n\n{body}")
