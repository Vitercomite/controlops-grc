"""Database access helpers (SQLite)."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.environ.get("CONTROLOPS_DB", ROOT / "data" / "controlops.db"))
EVIDENCE_DIR = ROOT / "data" / "evidence"
SCHEMA = ROOT / "database" / "schema.sql"
SEED = ROOT / "database" / "seed.sql"


def connect(path: str | Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path or DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection, seed: bool = True) -> None:
    """Create schema; load demo data only when the database is empty."""
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    empty = conn.execute("SELECT COUNT(*) FROM controls").fetchone()[0] == 0
    if seed and empty:
        conn.executescript(SEED.read_text(encoding="utf-8"))
    conn.commit()


def query_df(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> pd.DataFrame:
    return pd.read_sql_query(sql, conn, params=params)
