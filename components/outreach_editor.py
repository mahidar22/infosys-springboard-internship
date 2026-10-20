from __future__ import annotations
import html,json
import streamlit as st

def copy_widget(text:str,key:str)->None:
    """Browser clipboard control; no success claim is displayed because permission is browser-dependent."""
    safe=json.dumps(text)
    component=f'''<button id="copy-{key}" style="padding:7px 12px;border:1px solid #cbd5e1;border-radius:7px;background:white;cursor:pointer">Copy content</button><span id="note-{key}" style="margin-left:8px;font:12px sans-serif"></span><script>const b=document.getElementById("copy-{key}");b.onclick=async()=>{{try{{await navigator.clipboard.writeText({safe});document.getElementById("note-{key}").textContent="Copied";}}catch(e){{document.getElementById("note-{key}").textContent="Clipboard permission unavailable — use the copy icon in the text box.";}}}};</script>'''
    st.components.v1.html(component,height=42)

def draft_editor(draft, key_prefix:str="outreach") -> tuple[str|None,str]:
    subject=None
    if draft.subject_line is not None: subject=st.text_input("Subject line",value=draft.subject_line,key=f"{key_prefix}_subject")
    body=st.text_area("Draft",value=draft.body,height=280,key=f"{key_prefix}_body")
    copy_widget((subject+"\n\n" if subject else "")+body,f"{key_prefix}-copy")
    with st.expander("Personalization, facts, and assumptions"):
        st.write("**Personalization rationale**");st.write(draft.personalization_rationale or ["None"])
        st.write("**Facts used**");st.write([x.statement for x in draft.facts_used] or ["No specific facts used"])
        st.write("**Assumptions**");st.write(draft.assumptions or ["None"])
        st.write("**Missing context**");st.write(draft.missing_context or ["None"])
    return subject,body
