from datetime import date

import plotly.express as px
import streamlit as st

import db
import workflow
from ui import badge

COLORS = {"PASS": "#2e9e5b", "FAIL": "#d64545", "PENDING": "#e0a800"}


def render(conn):
    st.title("IT Controls Dashboard")
    st.caption("Control → Test → Evidence → Result → Finding → Remediation → Retest")
    m = workflow.get_metrics(conn)

    c = st.columns(3)
    c[0].metric("Controls Tested", m["controls"])
    c[1].metric("Passed", m["passed"])
    c[2].metric("Failed", m["failed"])
    c = st.columns(3)
    c[0].metric("Pending", m["pending"])
    c[1].metric("Open Findings", m["open_findings"])
    c[2].metric("Overdue Findings", m["overdue_findings"], delta_color="inverse")

    left, right = st.columns(2)
    status = db.query_df(conn, "SELECT status, COUNT(*) AS n FROM v_control_status GROUP BY status")
    fig = px.pie(status, names="status", values="n", hole=0.55, color="status",
                 color_discrete_map=COLORS, title="Control results")
    left.plotly_chart(fig, use_container_width=True)

    sev = db.query_df(conn, "SELECT severity, status, COUNT(*) AS n FROM findings GROUP BY severity, status")
    fig = px.bar(sev, x="severity", y="n", color="status", title="Findings by severity",
                 category_orders={"severity": list(workflow.SEVERITIES)})
    right.plotly_chart(fig, use_container_width=True)

    st.subheader("Overdue findings")
    overdue = db.query_df(
        conn,
        "SELECT id AS '#', control_id AS Control, title AS Title, severity AS Severity, owner AS Owner,"
        " due_date AS 'Due date', status AS Status FROM findings"
        " WHERE status != 'CLOSED' AND due_date < ? ORDER BY due_date",
        (date.today().isoformat(),),
    )
    if overdue.empty:
        st.success("No overdue findings.")
    else:
        overdue["Status"] = overdue["Status"].map(badge)
        st.dataframe(overdue, hide_index=True, use_container_width=True)

    st.subheader("Recent activity")
    hist = db.query_df(
        conn,
        "SELECT h.changed_on AS Date, 'Finding #' || h.finding_id AS Finding, h.from_status AS 'From',"
        " h.to_status AS 'To', h.note AS Note FROM finding_history h ORDER BY h.changed_on DESC, h.id DESC LIMIT 8",
    )
    st.dataframe(hist, hide_index=True, use_container_width=True)
