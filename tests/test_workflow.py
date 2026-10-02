import pytest

import workflow
from conftest import TODAY


def status(conn, fid):
    return conn.execute("SELECT status FROM findings WHERE id=?", (fid,)).fetchone()[0]


def test_dashboard_metrics(conn):
    m = workflow.get_metrics(conn, TODAY)
    assert m == {"controls": 10, "passed": 6, "failed": 3, "pending": 1,
                 "open_findings": 3, "overdue_findings": 2}


def test_control_status_uses_latest_test(conn):
    # IAM-001 failed initially, then passed on retest
    row = conn.execute("SELECT status FROM v_control_status WHERE id='IAM-001'").fetchone()
    assert row[0] == "PASS"


def test_control_without_test_is_pending(conn):
    conn.execute("INSERT INTO controls VALUES ('X-1','n','d','o','r','p','own','Quarterly')")
    assert conn.execute("SELECT status FROM v_control_status WHERE id='X-1'").fetchone()[0] == "PENDING"


def test_open_requires_plan_before_remediation(conn):
    with pytest.raises(workflow.WorkflowError, match="remediation plan"):
        workflow.advance(conn, 1, "IN_REMEDIATION", today=TODAY)


def test_full_lifecycle_closes_with_passing_retest(conn):
    workflow.update_plan(conn, 1, "Remove unapproved admin roles.", "2026-10-15", "Infrastructure Security")
    workflow.advance(conn, 1, "IN_REMEDIATION", today=TODAY)
    workflow.advance(conn, 1, "READY_FOR_RETEST", today=TODAY)
    assert workflow.record_retest(conn, 1, "PASS", "GRC Analyst", today=TODAY) == "CLOSED"
    f = conn.execute("SELECT * FROM findings WHERE id=1").fetchone()
    assert (f["status"], f["retest_result"], f["closed_on"]) == ("CLOSED", "PASS", "2026-10-01")
    assert conn.execute("SELECT status FROM v_control_status WHERE id='IAM-002'").fetchone()[0] == "PASS"
    assert conn.execute("SELECT COUNT(*) FROM finding_history WHERE finding_id=1").fetchone()[0] == 4


def test_failed_retest_reopens_remediation(conn):
    workflow.update_plan(conn, 1, "Plan", "2026-10-15", "Sec")
    workflow.advance(conn, 1, "IN_REMEDIATION", today=TODAY)
    workflow.advance(conn, 1, "READY_FOR_RETEST", today=TODAY)
    assert workflow.record_retest(conn, 1, "FAIL", "GRC Analyst", today=TODAY) == "IN_REMEDIATION"
    assert conn.execute("SELECT closed_on FROM findings WHERE id=1").fetchone()[0] is None


def test_cannot_close_directly(conn):
    with pytest.raises(workflow.WorkflowError):
        workflow.advance(conn, 2, "CLOSED")


def test_cannot_retest_unless_ready(conn):
    with pytest.raises(workflow.WorkflowError, match="READY_FOR_RETEST"):
        workflow.record_retest(conn, 2, "PASS", "GRC Analyst")


def test_invalid_transition_rejected(conn):
    with pytest.raises(workflow.WorkflowError, match="Invalid transition"):
        workflow.advance(conn, 1, "READY_FOR_RETEST")


def test_closed_finding_is_immutable(conn):
    with pytest.raises(workflow.WorkflowError):
        workflow.update_plan(conn, 3, "x", "2026-12-01", "IAM Team")


def test_open_finding_validates_and_logs(conn):
    tid = workflow.record_test(conn, "CM-002", "FAIL", "GRC Analyst", notes="No post-review", today=TODAY)
    fid = workflow.open_finding(conn, "CM-002", "No emergency review", "HIGH", "Missing", "CAB", "2026-11-01", tid, TODAY)
    assert status(conn, fid) == "OPEN"
    with pytest.raises(workflow.WorkflowError):
        workflow.open_finding(conn, "CM-002", "t", "SEVERE", "d", "o", "2026-11-01")
    with pytest.raises(workflow.WorkflowError):
        workflow.open_finding(conn, "CM-002", "t", "LOW", "d", "o", "01/11/2026")
