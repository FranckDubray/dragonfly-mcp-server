# Crash logger: logs complete context snapshots on errors
# Critical for debugging production issues

import sqlite3
import json
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, Optional

def _utcnow_str() -> str:
    """UTC ISO8601 microseconds"""
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')

def _sanitize_context(ctx: Dict[str, Any], max_size: int = 100000) -> str:
    """
    Sanitize and serialize context (mask PII, limit size).
    
    Args:
        ctx: Context dict (worker_ctx or cycle_ctx)
        max_size: Max JSON size in bytes (default: 100KB)
    
    Returns:
        JSON string (sanitized, truncated if needed)
    """
    try:
        # Deep copy to avoid mutating original
        import copy
        sanitized = copy.deepcopy(ctx)
        
        # TODO: Implement PII masking (emails, tokens, passwords)
        # For now: basic serialization with truncation
        
        json_str = json.dumps(sanitized, separators=(',', ':'), ensure_ascii=False)
        
        # Truncate if too large
        if len(json_str) > max_size:
            truncated = json_str[:max_size]
            # Try to close JSON properly
            if truncated.count('{') > truncated.count('}'):
                truncated += '}'
            if truncated.count('[') > truncated.count(']'):
                truncated += ']'
            json_str = truncated + f'\n... (truncated, original size: {len(json_str)} bytes)'
        
        return json_str
    
    except Exception as e:
        # Fallback: return error message if serialization fails
        return json.dumps({"error": f"Failed to serialize context: {str(e)[:200]}"})


def log_crash(
    db_path: str,
    worker: str,
    cycle_id: str,
    node: str,
    error: Exception,
    worker_ctx: Dict[str, Any],
    cycle_ctx: Dict[str, Any]
) -> None:
    """
    Log a crash with complete context snapshot.
    
    Args:
        db_path: SQLite DB path
        worker: Worker name
        cycle_id: Cycle ID
        node: Node name where crash occurred
        error: Exception object
        worker_ctx: Worker context (read-only constants)
        cycle_ctx: Cycle context (current state)
    
    Side-effects:
        Inserts row in crash_logs table with full context dumps
    """
    crashed_at = _utcnow_str()
    error_message = str(error)[:2000]  # Truncate to 2KB
    error_type = type(error).__name__
    error_code = getattr(error, 'code', None)
    
    # Get stack trace
    stack_trace = ''.join(traceback.format_tb(error.__traceback__))[:5000]  # Truncate to 5KB
    
    # Serialize contexts (with sanitization)
    worker_ctx_json = _sanitize_context(worker_ctx, max_size=50000)  # 50KB max
    cycle_ctx_json = _sanitize_context(cycle_ctx, max_size=100000)  # 100KB max
    
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
            INSERT INTO crash_logs (
                worker, cycle_id, node, crashed_at, error_message,
                error_type, error_code, worker_ctx_json, cycle_ctx_json, stack_trace
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            worker, cycle_id, node, crashed_at, error_message,
            error_type, error_code, worker_ctx_json, cycle_ctx_json, stack_trace
        ))
        conn.commit()
    finally:
        conn.close()


def get_recent_crashes(db_path: str, worker: str, limit: int = 10) -> list:
    """
    Get recent crash logs for a worker.
    
    Args:
        db_path: SQLite DB path
        worker: Worker name
        limit: Max number of crashes to return
    
    Returns:
        List of crash dicts (most recent first)
    """
    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.execute("""
            SELECT id, worker, cycle_id, node, crashed_at, error_message,
                   error_type, error_code, worker_ctx_json, cycle_ctx_json, stack_trace
            FROM crash_logs
            WHERE worker = ?
            ORDER BY crashed_at DESC
            LIMIT ?
        """, (worker, limit))
        
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
