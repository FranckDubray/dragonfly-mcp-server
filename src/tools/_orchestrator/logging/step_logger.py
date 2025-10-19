# Per-node step logging (job_steps table)

import sqlite3
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

def _utcnow_str() -> str:
    """UTC ISO8601 microseconds"""
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')

def begin_step(db_path: str, worker: str, cycle_id: str, node: str, handler_kind: Optional[str] = None) -> None:
    """
    Log step begin (insert row with status='running').
    
    Args:
        db_path: SQLite DB path
        worker: Worker name
        cycle_id: Cycle ID (e.g., "cycle_001")
        node: Node name
        handler_kind: Handler kind (optional, for io/transform nodes)
    """
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
            INSERT INTO job_steps (worker, cycle_id, node, handler_kind, status, started_at)
            VALUES (?, ?, ?, ?, 'running', ?)
        """, (worker, cycle_id, node, handler_kind, _utcnow_str()))
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
    
    Args:
        db_path: SQLite DB path
        worker: Worker name
        cycle_id: Cycle ID
        node: Node name
        status: Final status ('succeeded' | 'failed' | 'skipped')
        started_at: Start timestamp (UTC ISO8601)
        details: Optional details dict (compact JSON)
    """
    finished_at = _utcnow_str()
    
    # Compute duration_ms
    try:
        start_dt = datetime.fromisoformat(started_at.replace(' ', 'T'))
        finish_dt = datetime.fromisoformat(finished_at.replace(' ', 'T'))
        duration_ms = int((finish_dt - start_dt).total_seconds() * 1000)
    except:
        duration_ms = None
    
    # Serialize details (compact)
    details_json = json.dumps(details, separators=(',', ':')) if details else None
    
    # Extract edge_taken if present
    edge_taken = details.get('edge_taken') if details else None
    
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
            UPDATE job_steps
            SET status = ?, finished_at = ?, duration_ms = ?, edge_taken = ?, details_json = ?
            WHERE worker = ? AND cycle_id = ? AND node = ? AND status = 'running'
        """, (status, finished_at, duration_ms, edge_taken, details_json, worker, cycle_id, node))
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
    
    Args:
        db_path: SQLite DB path
        worker: Worker name
        cycle_id: Cycle ID
        node: Node name
        attempt: Attempt number (1, 2, 3...)
        error_message: Error message (truncated)
        error_code: Error code (e.g., 'TIMEOUT', 'HTTP_500')
        retry_after_sec: Backoff delay before next retry
    """
    conn = sqlite3.connect(db_path)
    try:
        details = {
            "retry_attempt": attempt,
            "error": {
                "message": error_message[:400],
                "code": error_code
            },
            "retry_after_sec": retry_after_sec
        }
        
        # Insert a 'skipped' step (intermediate log between begin/end)
        conn.execute("""
            INSERT INTO job_steps (
                worker, cycle_id, node, handler_kind, status, 
                started_at, finished_at, duration_ms, details_json
            ) VALUES (?, ?, ?, ?, 'skipped', ?, ?, 0, ?)
        """, (
            worker, cycle_id, f"{node}_retry_{attempt}", None,
            _utcnow_str(), _utcnow_str(), 
            json.dumps(details, separators=(',', ':'))
        ))
        conn.commit()
    finally:
        conn.close()
