from __future__ import annotations
from typing import Any
import streamlit as st

def bullets(title:str,items:list[Any],kind:str="") -> None:
    st.markdown(f"#### {title}")
    if not items: st.caption("None identified from the available context."); return
    for item in items:
        if hasattr(item,"model_dump"): item=item.model_dump()
        if isinstance(item,dict):
            text=item.get("statement") or item.get("action") or str(item)
            suffix=(f" — {item.get('rationale')}" if item.get("rationale") else "")
        else:text=str(item);suffix=""
        if kind in {"fact","hypothesis"}: st.markdown(f'<div class="sg-{kind}">{text}{suffix}</div>',unsafe_allow_html=True)
        else: st.markdown(f"- {text}{suffix}")

def research_panel(research:Any,qualification:Any|None=None)->None:
    st.subheader("Company & prospect analysis")
    st.write(research.company_overview)
    st.caption(research.disclaimer)
    c1,c2=st.columns(2)
    with c1: bullets("Source-supported facts",research.supported_facts,"fact"); bullets("Potential challenges — hypotheses",research.potential_challenges,"hypothesis"); bullets("Possible needs — hypotheses",research.possible_needs,"hypothesis")
    with c2: bullets("Sales opportunities — hypotheses",research.opportunities,"hypothesis"); st.markdown("#### Product & industry fit");st.write(research.product_industry_fit);st.markdown("#### Buyer-role relevance");st.write(research.buyer_role_relevance)
    bullets("Qualification insights",research.qualification_insights);bullets("Recommended discovery questions",research.discovery_questions);bullets("Missing information",research.missing_information)
    st.caption(f"Analysis confidence: **{research.confidence.title()}**")
    if qualification:
        st.divider();st.subheader("Qualification assessment")
        st.write(f"**{qualification.category}** — {qualification.fit_assessment}")
        c1,c2=st.columns(2)
        with c1:bullets("Positive signals",qualification.positive_signals)
        with c2:bullets("Risks & gaps",qualification.risks_or_gaps)
        st.write(f"**Next step:** {qualification.recommended_next_step}")

def recommendation_card(rec:dict,on_complete=None,on_dismiss=None,on_draft=None)->None:
    with st.container(border=True):
        top=st.columns([3,1,1]);top[0].markdown(f"**{rec.get('related_lead','Lead')}** · {rec.get('priority','—')} priority");top[1].caption(rec.get('status','Open'));top[2].caption(rec.get('suggested_timing') or "Timing not established")
        st.write(rec.get("recommended_action",""));st.caption(rec.get("reason",""))
        evidence=rec.get("supporting_evidence",[])
        if evidence: st.caption("Evidence: "+"; ".join(x.get("statement",str(x)) if isinstance(x,dict) else str(x) for x in evidence))
        a,b,c=st.columns(3)
        if on_complete and a.button("Mark complete",key=f"complete-{rec['id']}"):on_complete(rec)
        if on_dismiss and b.button("Dismiss",key=f"dismiss-{rec['id']}"):on_dismiss(rec)
        if on_draft and c.button("Generate follow-up draft",key=f"draft-{rec['id']}"):on_draft(rec)
