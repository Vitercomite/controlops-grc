from datetime import date

import streamlit as st

import db
import workflow
from ui import badge

NEXT_LABEL = {"OPEN": "Start remediation", "IN_REMEDIATION": "Mark ready for retest",
              "READY_FOR_RETEST": "Send back to remediation"}


def render(conn):
    st.title("Remediation & Retest")
    rows = conn.execute("SELECT id, title, status FROM findings WHERE status != 'CLOSED' ORDER BY due_date").fetchall()
    if not rows:
        st.success("All findings are closed.")
        return
    fid = st.selectbox("Finding", [r["id"] for r in rows],
                       format_func=lambda i: next(f"#{r['id']:03d} — {r['title']} [{r['status']}]" for r in rows if r["id"] == i))
    f = conn.execute("SELECT * FROM findings WHERE id=?", (fid,)).fetchone()

    steps = list(workflow.STATUSES)
    st.progress(steps.index(f["status"]) / (len(steps) - 1), text=f"Status: {badge(f['status'])}")

    with st.form("plan"):
        plan = st.text_area("Remediation plan", value=f["remediation_plan"] or "")
        owner = st.text_input("Owner", value=f["owner"])
        due = st.date_input("Due date", value=date.fromisoformat(f["due_date"]))
        if st.form_submit_button("Save plan"):
            try:
                workflow.update_plan(conn, fid, plan, due.isoformat(), owner)
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    note = st.text_input("Status change note", key=f"note_{fid}")
    if f["status"] in NEXT_LABEL and st.button(NEXT_LABEL[f["status"]]):
        target = {"OPEN": "IN_REMEDIATION", "IN_REMEDIATION": "READY_FOR_RETEST", "READY_FOR_RETEST": "IN_REMEDIATION"}[f["status"]]
        try:
            workflow.advance(conn, fid, target, note)
            st.rerun()
        except workflow.WorkflowError as exc:
            st.error(str(exc))

    if f["status"] == "READY_FOR_RETEST":
        st.subheader("Retest")
        ev = conn.execute("SELECT id, filename FROM evidence WHERE control_id=? ORDER BY id DESC", (f["control_id"],)).fetchall()
        with st.form("retest"):
            result = st.radio("Retest result", ["PASS", "FAIL"], horizontal=True)
            tester = st.text_input("Tester", value="GRC Analyst")
            ev_id = st.selectbox("Evidence", [e["id"] for e in ev], format_func=lambda i: next(e["filename"] for e in ev if e["id"] == i)) if ev else None
            notes = st.text_area("Notes")
            if st.form_submit_button("Record retest"):
                try:
                    new = workflow.record_retest(conn, fid, result, tester, ev_id, notes)
                    st.success(f"Finding is now {new}.")
                    st.rerun()
                except workflow.WorkflowError as exc:
                    st.error(str(exc))

    st.subheader("History")
    hist = db.query_df(conn, "SELECT changed_on AS Date, from_status AS 'From', to_status AS 'To', note AS Note"
                             " FROM finding_history WHERE finding_id=? ORDER BY id", (fid,))
    st.dataframe(hist, hide_index=True, use_container_width=True)
