





















# Per-node step logging (job_steps table)

import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Centralized time + sanitation utilities
from ..utils import utcnow_str
from ..engine.debug_utils import sanitize_details_for_log

def begin_step(db_path: str, worker: str, cycle_id: str, node: str, handler_kind: Optional[str] = None) -> None:
    """
    Log step begin (insert row with status='running').
    """
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO job_steps (worker, cycle_id, node, handler_kind, status, started_at)
            VALUES (?, ?, ?, ?, 'running', ?)
            """,
            (worker, cycle_id, node, handler_kind, utcnow_str())
        )
        conn.commit()
    finally:
        conn.close()


def end_step(
    db_path: str,
    worker: str,
    cycle_id: str,
    node: str,
    status: str,
    started_at: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log step end (update row with status, duration, details).
    """
    finished_at = utcnow_str()
    
    # Compute duration_ms
    try:
        start_dt = datetime.fromisoformat(started_at.replace(' ', 'T'))
        finish_dt = datetime.fromisoformat(finished_at.replace(' ', 'T'))
        duration_ms = int((finish_dt - start_dt).total_seconds() * 1000)
    except Exception:
        duration_ms = None
    
    # Sanitize details
    clean_details = sanitize_details_for_log(details or {}, max_bytes=10_000)
    try:
        details_json = json.dumps(clean_details, separators=(',', ':'), ensure_ascii=False)
    except Exception:
        details_json = json.dumps({"error": "failed to serialize details"})
    
    # Extract edge_taken if present in details
    edge_taken = None
    try:
        edge_taken = (details or {}).get('edge_taken')
    except Exception:
        edge_taken = None
    
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            UPDATE job_steps
            SET status = ?, finished_at = ?, duration_ms = ?, edge_taken = ?, details_json = ?
            WHERE worker = ? AND cycle_id = ? AND node = ? AND status = 'running'
            """,
            (status, finished_at, duration_ms, edge_taken, details_json, worker, cycle_id, node)
        )
        conn.commit()
    finally:
        conn.close()


def log_retry_attempt(
    db_path: str,
    worker: str,
    cycle_id: str,
    node: str,
    attempt: int,
    error_message: str,
    error_code: str,
    retry_after_sec: float
) -> None:
    """
    Log a retry attempt (insert intermediate log).
    """
    conn = sqlite3.connect(db_path)
    try:
        details = {
            "retry_attempt": attempt,
            "error": {"message": (error_message or "")[:400], "code": error_code},
            "retry_after_sec": retry_after_sec
        }
        details_json = json.dumps(details, separators=(',', ':'))
        
        # Insert a 'skipped' step (intermediate log between begin/end)
        conn.execute(
            """
            INSERT INTO job_steps (
                worker, cycle_id, node, handler_kind, status,
                started_at, finished_at, duration_ms, details_json
            ) VALUES (?, ?, ?, ?, 'skipped', ?, ?, 0, ?)
            """,
            (
                worker, cycle_id, f"{node}_retry_{attempt}", None,
                utcnow_str(), utcnow_str(),
                details_json
            )
        )
        conn.commit()
    finally:
        conn.close()
