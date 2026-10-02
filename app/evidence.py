import hashlib
import re
from datetime import date

import pandas as pd
import streamlit as st

import db


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render(conn):
    st.title("Evidence")
    df = db.query_df(
        conn,
        "SELECT e.id, e.control_id AS Control, e.filename AS File, e.description AS Description,"
        " e.collected_on AS Collected FROM evidence e ORDER BY e.collected_on DESC, e.id DESC",
    )
    st.dataframe(df.drop(columns="id"), hide_index=True, use_container_width=True)

    if not df.empty:
        eid = st.selectbox("Preview", df["id"], format_func=lambda i: df.set_index("id").loc[i, "File"])
        name = df.set_index("id").loc[eid, "File"]
        path = db.EVIDENCE_DIR / name
        if path.exists():
            st.caption(f"SHA-256 (integrity): `{_sha256(path)}`")
            if path.suffix == ".csv":
                st.dataframe(pd.read_csv(path), hide_index=True, use_container_width=True)
            else:
                st.code(path.read_text(errors="replace"))
        else:
            st.warning("File not found on disk.")

    with st.expander("Upload evidence"):
        with st.form("upload"):
            cid = st.selectbox("Control", [r[0] for r in conn.execute("SELECT id FROM controls ORDER BY id")])
            desc = st.text_input("Description")
            up = st.file_uploader("File (CSV, TXT, PDF, PNG)", type=["csv", "txt", "pdf", "png"])
            if st.form_submit_button("Upload") and up:
                safe = re.sub(r"[^A-Za-z0-9._-]", "_", up.name)
                dest = db.EVIDENCE_DIR / safe
                if dest.exists():
                    st.error("A file with this name already exists.")
                else:
                    dest.write_bytes(up.getvalue())
                    conn.execute("INSERT INTO evidence (control_id, filename, description, collected_on) VALUES (?,?,?,?)",
                                 (cid, safe, desc, date.today().isoformat()))
                    conn.commit()
                    st.rerun()
