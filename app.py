import streamlit as st
from components.common import apply_style
from components.sidebar import render_sidebar
from components.dashboard_view import render_dashboard

st.set_page_config(page_title="SalesGenie AI",page_icon="✨",layout="wide",initial_sidebar_state="expanded")
apply_style(); render_sidebar(); render_dashboard()
