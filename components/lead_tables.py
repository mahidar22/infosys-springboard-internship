from __future__ import annotations
import pandas as pd
import streamlit as st

def lead_table(leads:list[dict])->None:
    if not leads:
        st.info("No leads match the current filters."); return
    columns=["company_name","contact_name","industry","company_size","prospect_role","status","stage","email"]
    data=pd.DataFrame(leads)
    st.dataframe(data[[c for c in columns if c in data.columns]],use_container_width=True,hide_index=True,column_config={"company_name":"Company","contact_name":"Contact","prospect_role":"Role","company_size":"Size"})

def lead_profile(lead:dict)->None:
    st.subheader(lead.get("company_name","Lead"))
    cols=st.columns(4)
    for col,(label,key) in zip(cols,[("Contact","contact_name"),("Role","prospect_role"),("Stage","stage"),("Status","status")]): col.metric(label,lead.get(key) or "—")
    st.caption(f"{lead.get('industry') or 'Industry unknown'} · {lead.get('company_size') or 'Size unknown'}")
    if lead.get("company_description"): st.write(lead["company_description"])
