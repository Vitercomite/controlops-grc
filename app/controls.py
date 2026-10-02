from datetime import date, timedelta

import streamlit as st

import db
import workflow
from ui import badge


def render(conn):
    st.title("Controls")
    df = db.query_df(
        conn,
        "SELECT id AS ID, name AS Name, domain AS Domain, owner AS Owner, status AS Status,"
        " last_tested AS 'Last tested' FROM v_control_status ORDER BY id",
    )
    wanted = st.multiselect("Filter by status", ["PASS", "FAIL", "PENDING"], default=[])
    view = df[df["Status"].isin(wanted)] if wanted else df
    shown = view.copy()
    shown["Status"] = shown["Status"].map(badge)
    st.dataframe(shown, hide_index=True, use_container_width=True)

    st.divider()
    cid = st.selectbox("Control detail", df["ID"], format_func=lambda i: f"{i} — {df.set_index('ID').loc[i, 'Name']}")
    c = conn.execute("SELECT * FROM controls WHERE id=?", (cid,)).fetchone()
    last = conn.execute(
        "SELECT t.*, e.filename FROM control_tests t LEFT JOIN evidence e ON e.id=t.evidence_id"
        " WHERE t.control_id=? ORDER BY t.test_date DESC, t.id DESC LIMIT 1", (cid,)).fetchone()
    finding = conn.execute(
        "SELECT * FROM findings WHERE control_id=? ORDER BY id DESC LIMIT 1", (cid,)).fetchone()

    st.header(f"{c['id']} — {c['name']}")
    a, b = st.columns(2)
    a.markdown(f"**Objective**  \n{c['objective']}")
    a.markdown(f"**Risk**  \n{c['risk']}")
    a.markdown(f"**Test procedure**  \n{c['test_procedure']}")
    b.markdown(f"**Owner**  \n{c['owner']}")
    b.markdown(f"**Frequency**  \n{c['frequency']}")
    b.markdown(f"**Evidence**  \n{(last['filename'] if last and last['filename'] else '—')}")
    b.markdown(f"**Result**  \n{badge(last['result']) if last else badge('PENDING')}")
    if finding:
        st.info(
            f"**Finding #{finding['id']}** ({finding['severity']}): {finding['description']}  \n"
            f"Owner: {finding['owner']} · Due: {finding['due_date']} · Status: {badge(finding['status'])}"
        )

    with st.expander("Test history"):
        hist = db.query_df(
            conn,
            "SELECT t.test_date AS Date, t.result AS Result, CASE t.is_retest WHEN 1 THEN 'Retest' ELSE 'Initial' END AS Type,"
            " t.tester AS Tester, e.filename AS Evidence, t.notes AS Notes FROM control_tests t"
            " LEFT JOIN evidence e ON e.id=t.evidence_id WHERE t.control_id=? ORDER BY t.test_date DESC, t.id DESC",
            (cid,),
        )
        st.dataframe(hist, hide_index=True, use_container_width=True)

    with st.expander("Register a new test result"):
        ev = conn.execute("SELECT id, filename FROM evidence WHERE control_id=? ORDER BY id DESC", (cid,)).fetchall()
        with st.form(f"test_{cid}"):
            result = st.selectbox("Result", workflow.RESULTS)
            tester = st.text_input("Tester", value="GRC Analyst")
            ev_id = st.selectbox("Evidence", [None] + [e["id"] for e in ev],
                                 format_func=lambda i: "— none —" if i is None else next(e["filename"] for e in ev if e["id"] == i))
            notes = st.text_area("Notes")
            st.markdown("**If FAIL — finding details**")
            title = st.text_input("Finding title")
            sev = st.selectbox("Severity", workflow.SEVERITIES, index=1)
            due = st.date_input("Due date", value=date.today() + timedelta(days=30))
            if st.form_submit_button("Save test"):
                try:
                    if result == "PASS" and not ev_id:
                        raise workflow.WorkflowError("A PASS result requires evidence")
                    tid = workflow.record_test(conn, cid, result, tester, ev_id, notes)
                    if result == "FAIL":
                        workflow.open_finding(conn, cid, title, sev, notes or title, c["owner"], due.isoformat(), tid)
                    st.success("Saved.")
                    st.rerun()
                except workflow.WorkflowError as exc:
                    st.error(str(exc))
