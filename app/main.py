"""ControlOps GRC - entry point.  Run:  streamlit run app/main.py"""
import streamlit as st

import controls
import dashboard
import db
import evidence
import findings
import remediation

st.set_page_config(page_title="ControlOps GRC", page_icon="🛡️", layout="wide")


@st.cache_resource
def get_conn():
    db.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = db.connect()
    db.init_db(conn)
    return conn


PAGES = {
    "Dashboard": dashboard,
    "Controls": controls,
    "Findings": findings,
    "Remediation": remediation,
    "Evidence": evidence,
}

st.sidebar.title("🛡️ ControlOps")
st.sidebar.caption("GRC / IT Controls Proof of Concept")
page = st.sidebar.radio("Navigate", list(PAGES))
st.sidebar.divider()
st.sidebar.caption("Demo data is synthetic.")
PAGES[page].render(get_conn())
