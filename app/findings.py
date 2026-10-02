import streamlit as st

import db
import workflow
from ui import badge


def render(conn):
    st.title("Findings")
    df = db.query_df(
        conn,
        "SELECT id AS '#', control_id AS Control, title AS Title, severity AS Severity, owner AS Owner,"
        " due_date AS 'Due date', status AS Status FROM findings ORDER BY id",
    )
    c1, c2 = st.columns(2)
    sts = c1.multiselect("Status", workflow.STATUSES)
    sev = c2.multiselect("Severity", workflow.SEVERITIES)
    if sts:
        df = df[df["Status"].isin(sts)]
    if sev:
        df = df[df["Severity"].isin(sev)]
    shown = df.copy()
    shown["Status"] = shown["Status"].map(badge)
    shown["Severity"] = shown["Severity"].map(badge)
    st.dataframe(shown, hide_index=True, use_container_width=True)
    if df.empty:
        return

    fid = st.selectbox("Finding detail", df["#"], format_func=lambda i: f"#{i:03d} — {df.set_index('#').loc[i, 'Title']}")
    f = conn.execute("SELECT * FROM findings WHERE id=?", (int(fid),)).fetchone()
    st.header(f"Finding #{f['id']:03d} — {f['title']}")
    a, b = st.columns(2)
    a.markdown(f"**Control**  \n{f['control_id']}")
    a.markdown(f"**Severity**  \n{badge(f['severity'])}")
    a.markdown(f"**Description**  \n{f['description']}")
    a.markdown(f"**Remediation plan**  \n{f['remediation_plan'] or '— not yet defined —'}")
    b.markdown(f"**Owner**  \n{f['owner']}")
    b.markdown(f"**Due date**  \n{f['due_date']}")
    b.markdown(f"**Status**  \n{badge(f['status'])}")
    b.markdown(f"**Retest result**  \n{f['retest_result'] or '—'}")
    ev = conn.execute(
        "SELECT e.filename FROM control_tests t JOIN evidence e ON e.id=t.evidence_id WHERE t.id=?", (f["test_id"],)
    ).fetchone()
    b.markdown(f"**Evidence**  \n{ev['filename'] if ev else '—'}")
    st.caption("Manage remediation and retest in the Remediation page.")
