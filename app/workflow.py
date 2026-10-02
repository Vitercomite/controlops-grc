"""Business rules: test recording, finding lifecycle, retest and metrics.

Kept free of Streamlit imports so it can be unit-tested.
Lifecycle: OPEN -> IN_REMEDIATION -> READY_FOR_RETEST -> CLOSED (only via a passing retest).
A failing retest sends the finding back to IN_REMEDIATION.
"""
from __future__ import annotations

import sqlite3
from datetime import date

STATUSES = ("OPEN", "IN_REMEDIATION", "READY_FOR_RETEST", "CLOSED")
SEVERITIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
RESULTS = ("PASS", "FAIL", "PENDING")
TRANSITIONS = {
    "OPEN": {"IN_REMEDIATION"},
    "IN_REMEDIATION": {"READY_FOR_RETEST"},
    "READY_FOR_RETEST": {"IN_REMEDIATION"},  # CLOSED is reachable only through record_retest()
    "CLOSED": set(),
}


class WorkflowError(ValueError):
    """Raised when an action violates the control-testing workflow."""


def _iso(today: date | None) -> str:
    return (today or date.today()).isoformat()


def _log(conn, finding_id, from_status, to_status, note, today):
    conn.execute(
        "INSERT INTO finding_history (finding_id, changed_on, from_status, to_status, note) VALUES (?,?,?,?,?)",
        (finding_id, _iso(today), from_status, to_status, note),
    )


def _finding(conn, finding_id):
    row = conn.execute("SELECT * FROM findings WHERE id = ?", (finding_id,)).fetchone()
    if row is None:
        raise WorkflowError(f"Finding {finding_id} not found")
    return row


def get_metrics(conn: sqlite3.Connection, today: date | None = None) -> dict:
    counts = dict(conn.execute("SELECT status, COUNT(*) FROM v_control_status GROUP BY status").fetchall())
    open_f = conn.execute("SELECT COUNT(*) FROM findings WHERE status != 'CLOSED'").fetchone()[0]
    overdue = conn.execute(
        "SELECT COUNT(*) FROM findings WHERE status != 'CLOSED' AND due_date < ?", (_iso(today),)
    ).fetchone()[0]
    return {
        "controls": sum(counts.values()),
        "passed": counts.get("PASS", 0),
        "failed": counts.get("FAIL", 0),
        "pending": counts.get("PENDING", 0),
        "open_findings": open_f,
        "overdue_findings": overdue,
    }


def record_test(conn, control_id, result, tester, evidence_id=None, notes="", is_retest=False, today=None) -> int:
    if result not in RESULTS:
        raise WorkflowError(f"Invalid result: {result}")
    cur = conn.execute(
        "INSERT INTO control_tests (control_id, test_date, tester, result, evidence_id, notes, is_retest)"
        " VALUES (?,?,?,?,?,?,?)",
        (control_id, _iso(today), tester, result, evidence_id, notes, int(is_retest)),
    )
    conn.commit()
    return cur.lastrowid


def open_finding(conn, control_id, title, severity, description, owner, due_date, test_id=None, today=None) -> int:
    if severity not in SEVERITIES:
        raise WorkflowError(f"Invalid severity: {severity}")
    if not title.strip() or not description.strip():
        raise WorkflowError("Title and description are required")
    try:
        date.fromisoformat(due_date)
    except ValueError as exc:
        raise WorkflowError("due_date must be YYYY-MM-DD") from exc
    cur = conn.execute(
        "INSERT INTO findings (control_id, test_id, title, severity, description, owner, due_date, status, opened_on)"
        " VALUES (?,?,?,?,?,?,?,'OPEN',?)",
        (control_id, test_id, title.strip(), severity, description.strip(), owner, due_date, _iso(today)),
    )
    _log(conn, cur.lastrowid, None, "OPEN", "Finding opened from failed test.", today)
    conn.commit()
    return cur.lastrowid


def update_plan(conn, finding_id, remediation_plan, due_date, owner) -> None:
    f = _finding(conn, finding_id)
    if f["status"] == "CLOSED":
        raise WorkflowError("Closed findings cannot be edited")
    date.fromisoformat(due_date)
    conn.execute(
        "UPDATE findings SET remediation_plan=?, due_date=?, owner=? WHERE id=?",
        (remediation_plan.strip(), due_date, owner, finding_id),
    )
    conn.commit()


def advance(conn, finding_id, new_status, note="", today=None) -> None:
    f = _finding(conn, finding_id)
    current = f["status"]
    if new_status == "CLOSED":
        raise WorkflowError("A finding can only be closed through a passing retest")
    if new_status not in TRANSITIONS.get(current, set()):
        raise WorkflowError(f"Invalid transition {current} -> {new_status}")
    if new_status == "IN_REMEDIATION" and current == "OPEN" and not (f["remediation_plan"] or "").strip():
        raise WorkflowError("A remediation plan is required before starting remediation")
    conn.execute("UPDATE findings SET status=? WHERE id=?", (new_status, finding_id))
    _log(conn, finding_id, current, new_status, note, today)
    conn.commit()


def record_retest(conn, finding_id, result, tester, evidence_id=None, notes="", today=None) -> str:
    """Retest a finding. PASS closes it; FAIL returns it to IN_REMEDIATION. Returns the new status."""
    f = _finding(conn, finding_id)
    if f["status"] != "READY_FOR_RETEST":
        raise WorkflowError("Finding must be READY_FOR_RETEST to be retested")
    if result not in ("PASS", "FAIL"):
        raise WorkflowError("Retest result must be PASS or FAIL")
    record_test(conn, f["control_id"], result, tester, evidence_id, notes, is_retest=True, today=today)
    new_status = "CLOSED" if result == "PASS" else "IN_REMEDIATION"
    closed_on = _iso(today) if result == "PASS" else None
    conn.execute(
        "UPDATE findings SET status=?, retest_result=?, closed_on=? WHERE id=?",
        (new_status, result, closed_on, finding_id),
    )
    _log(conn, finding_id, "READY_FOR_RETEST", new_status, f"Retest {result}. {notes}".strip(), today)
    conn.commit()
    return new_status
