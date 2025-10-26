











import sqlite3
from typing import Optional

SCHEMA_CHANGES = {
    "job_steps": [
        {"col": "run_id", "type": "TEXT"},
    ]
}

TRIGGER_SQL = (
    """
    CREATE TRIGGER IF NOT EXISTS job_steps_set_run_id
    AFTER INSERT ON job_steps
    BEGIN
      UPDATE job_steps
      SET run_id = (
        SELECT svalue FROM job_state_kv WHERE skey='run_id' LIMIT 1
      )
      WHERE rowid = NEW.rowid AND run_id IS NULL;
    END;
    """
)

INDEX_SQL = (
    "CREATE INDEX IF NOT EXISTS idx_job_steps_worker_runid ON job_steps(worker, run_id);"
)

BACKFILL_SQL = (
    """
    UPDATE job_steps
    SET run_id = (
      SELECT ra.run_id FROM run_audit ra
      WHERE ra.worker = job_steps.worker
        AND (ra.started_at IS NULL OR ra.started_at <= job_steps.started_at)
        AND (ra.ended_at IS NULL OR ra.ended_at >= job_steps.started_at)
      ORDER BY ra.started_at DESC
      LIMIT 1
    )
    WHERE run_id IS NULL;
    """
)


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    try:
        cur = conn.execute(f"PRAGMA table_info({table})")
        cols = [row[1] for row in cur.fetchall()]  # (cid, name, type, notnull, dflt_value, pk)
        return column in cols
    except Exception:
        return False


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    try:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
        )
        return cur.fetchone() is not None
    except Exception:
        return False


def ensure_migrations(db_path: str) -> None:
    """Idempotent migrations: add job_steps.run_id, create index and trigger, backfill existing rows.
    Safe to call at each start.
    """
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            # 1) Ensure table exists before altering
            if _table_exists(conn, "job_steps"):
                # 1.a) Add missing columns
                for change in SCHEMA_CHANGES.get("job_steps", []):
                    col = change.get("col")
                    coltype = change.get("type") or "TEXT"
                    if col and not _column_exists(conn, "job_steps", col):
                        conn.execute(f"ALTER TABLE job_steps ADD COLUMN {col} {coltype}")
                # 1.b) Index for worker+run_id
                conn.execute(INDEX_SQL)
                # 1.c) Trigger to set run_id from KV at insert time
                conn.executescript(TRIGGER_SQL)
                # 1.d) Backfill run_id using run_audit window (best-effort)
                if _table_exists(conn, "run_audit"):
                    conn.execute(BACKFILL_SQL)
            conn.commit()
        finally:
            conn.close()
    except Exception:
        # Best effort: never crash the server on migration
        pass

