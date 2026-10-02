-- ControlOps GRC schema (SQLite). PostgreSQL-friendly: swap AUTOINCREMENT for SERIAL.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS controls (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    domain          TEXT NOT NULL,
    objective       TEXT NOT NULL,
    risk            TEXT NOT NULL,
    test_procedure  TEXT NOT NULL,
    owner           TEXT NOT NULL,
    frequency       TEXT NOT NULL DEFAULT 'Quarterly'
);

CREATE TABLE IF NOT EXISTS evidence (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    control_id    TEXT NOT NULL REFERENCES controls(id),
    filename      TEXT NOT NULL UNIQUE,
    description   TEXT,
    collected_on  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS control_tests (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    control_id   TEXT NOT NULL REFERENCES controls(id),
    test_date    TEXT NOT NULL,
    tester       TEXT NOT NULL,
    result       TEXT NOT NULL CHECK (result IN ('PASS','FAIL','PENDING')),
    evidence_id  INTEGER REFERENCES evidence(id),
    notes        TEXT,
    is_retest    INTEGER NOT NULL DEFAULT 0 CHECK (is_retest IN (0,1))
);

CREATE TABLE IF NOT EXISTS findings (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    control_id        TEXT NOT NULL REFERENCES controls(id),
    test_id           INTEGER REFERENCES control_tests(id),
    title             TEXT NOT NULL,
    severity          TEXT NOT NULL CHECK (severity IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    description       TEXT NOT NULL,
    owner             TEXT NOT NULL,
    remediation_plan  TEXT,
    due_date          TEXT NOT NULL,
    status            TEXT NOT NULL DEFAULT 'OPEN'
                      CHECK (status IN ('OPEN','IN_REMEDIATION','READY_FOR_RETEST','CLOSED')),
    opened_on         TEXT NOT NULL,
    closed_on         TEXT,
    retest_result     TEXT CHECK (retest_result IN ('PASS','FAIL') OR retest_result IS NULL)
);

-- Audit trail of every status change
CREATE TABLE IF NOT EXISTS finding_history (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    finding_id   INTEGER NOT NULL REFERENCES findings(id),
    changed_on   TEXT NOT NULL,
    from_status  TEXT,
    to_status    TEXT NOT NULL,
    note         TEXT
);

-- Current status of a control = result of its most recent test (no test = PENDING)
CREATE VIEW IF NOT EXISTS v_control_status AS
SELECT c.id, c.name, c.domain, c.owner,
       COALESCE(t.result, 'PENDING') AS status,
       t.test_date AS last_tested
FROM controls c
LEFT JOIN control_tests t ON t.id = (
    SELECT id FROM control_tests WHERE control_id = c.id
    ORDER BY test_date DESC, id DESC LIMIT 1
);
