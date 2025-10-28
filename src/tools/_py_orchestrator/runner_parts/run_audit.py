
import sqlite3
import json
from typing import Any, Dict
from ..db import get_state_kv
from ..utils.time import utcnow_str
from datetime import datetime

TS_FORMAT = "%Y-%m-%d %H:%M:%S.%f"  # close to utcnow_str()


def _parse_dt(s: str) -> datetime | None:
    if not s:
        return None
    # Try several formats gracefully
    for fmt in (TS_FORMAT, "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    return None


def _ensure_table(conn: sqlite3.Connection):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS run_audit (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          run_id TEXT,
          worker TEXT,
          pid TEXT,
          process_uid TEXT,
          started_at TEXT,
          ended_at TEXT,
          duration_ms INTEGER,
          status TEXT,
          last_error TEXT,
          last_node TEXT,
          steps_total INTEGER,
          steps_failed INTEGER,
          last_call_json TEXT,
          last_result_preview TEXT,
          metadata_json TEXT
        )
        """
    )


def persist_run_audit(db_path: str, worker: str, status: str) -> None:
    """Persist a compact, LLM-friendly run audit row in the same DB as the runner state."""
    try:
        conn = sqlite3.connect(db_path, timeout=3.0)
        try:
            _ensure_table(conn)
            # KV context
            run_id = get_state_kv(db_path, worker, 'run_id') or ''
            pid = get_state_kv(db_path, worker, 'pid') or ''
            process_uid = get_state_kv(db_path, worker, 'process_uid') or ''
            started = get_state_kv(db_path, worker, 'run_started_at') or ''
            ended = utcnow_str()
            dt_s = _parse_dt(started)
            dt_e = _parse_dt(ended)
            duration_ms = 0
            if dt_s and dt_e:
                duration_ms = int((dt_e - dt_s).total_seconds() * 1000)

            # Counts & last step/context
            steps_total = 0
            steps_failed = 0
            last_node = ''
            last_call_json = ''
            last_result_preview = ''

            try:
                # Steps in current run window (best effort)
                cur = conn.execute(
                    "SELECT COUNT(*) AS total, SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) AS failed "
                    "FROM job_steps WHERE worker=? AND started_at>=?",
                    (worker, started)
                )
                row = cur.fetchone()
                if row:
                    steps_total = int(row[0] or 0)
                    steps_failed = int(row[1] or 0)
            except Exception:
                pass

            try:
                cur = conn.execute(
                    "SELECT node, details_json FROM job_steps WHERE worker=? ORDER BY rowid DESC LIMIT 1",
                    (worker,)
                )
                row = cur.fetchone()
                if row:
                    last_node = row[0] or ''
                    dj = row[1]
                    if dj:
                        try:
                            obj = json.loads(dj)
                            call = obj.get('call') if isinstance(obj, dict) else None
                            lrp = obj.get('last_result_preview') if isinstance(obj, dict) else None
                            if call:
                                try:
                                    last_call_json = json.dumps(call)[:800]
                                except Exception:
                                    last_call_json = str(call)[:800]
                            if lrp is not None:
                                s = lrp if isinstance(lrp, str) else str(lrp)
                                last_result_preview = s[:800]
                        except Exception:
                            pass
            except Exception:
                pass

            # Metadata
            metadata_json = ''
            try:
                raw = get_state_kv(db_path, worker, 'py.process_metadata') or ''
                metadata_json = raw[:2000]
            except Exception:
                pass

            # last_error
            last_error = get_state_kv(db_path, worker, 'last_error') or ''

            conn.execute(
                """
                INSERT INTO run_audit (
                  run_id, worker, pid, process_uid, started_at, ended_at, duration_ms, status,
                  last_error, last_node, steps_total, steps_failed, last_call_json, last_result_preview, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id, worker, pid, process_uid, started, ended, duration_ms, status,
                    last_error[:400], last_node[:200], steps_total, steps_failed,
                    last_call_json, last_result_preview, metadata_json
                )
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        # Best effort: never crash the server on audit write
        pass
