
# Crash logger: logs complete context snapshots on errors
# Critical for debugging production issues

import sqlite3
import json
import traceback
import sys
from typing import Dict, Any, Optional, List

# Use centralized time and sanitation
from ..utils import utcnow_str
from ..engine.debug_utils import sanitize_details_for_log


def _sanitize_context(ctx: Dict[str, Any], max_size: int = 100000) -> str:
    """
    Sanitize and serialize context (mask PII, limit size).
    Returns a JSON string (possibly truncated with a note).
    """
    try:
        clean = sanitize_details_for_log(ctx, max_bytes=max_size)
        json_str = json.dumps(clean, separators=(',', ':'), ensure_ascii=False, default=str)
        if len(json_str) > max_size:
            return json_str[:max_size] + f"\n... (truncated, original size: {len(json_str)} bytes)"
        return json_str
    except Exception as e:
        return json.dumps({"error": f"Failed to serialize context: {str(e)[:200]}"})


def log_crash(db_path: str, worker: str, cycle_id: str, node: str,
              error: BaseException,
              worker_ctx: Optional[Dict[str, Any]] = None,
              cycle_ctx: Optional[Dict[str, Any]] = None) -> None:
    """
    Persist a crash entry with sanitized contexts and full traceback.
    """
    try:
        err_type = type(error).__name__ if error else None
        # Some engine errors may expose a code attribute
        err_code = getattr(error, 'code', None)
        err_msg = (str(error) or "")[:400]
        stack = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        # Cap traceback to ~20KB
        if len(stack) > 20_000:
            stack = stack[:20_000] + f"\n... (truncated, original size: {len(stack)} chars)"

        worker_ctx_json = _sanitize_context(worker_ctx or {}, max_size=100_000)
        cycle_ctx_json = _sanitize_context(cycle_ctx or {}, max_size=100_000)

        conn = sqlite3.connect(db_path, timeout=5.0)
        try:
            run_id = None
            try:
                c2 = conn.execute("SELECT svalue FROM job_state_kv WHERE worker=? AND skey=?", (worker, 'run_id'))
                r2 = c2.fetchone()
                run_id = r2[0] if r2 and r2[0] else ''
            except Exception:
                run_id = ''
            conn.execute(
                """
                INSERT INTO crash_logs (
                  worker, cycle_id, node, crashed_at,
                  error_message, error_type, error_code,
                  worker_ctx_json, cycle_ctx_json, stack_trace, run_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    worker or '__global__',
                    cycle_id or 'unknown',
                    node or 'unknown',
                    utcnow_str(),
                    err_msg,
                    err_type,
                    err_code if err_code is not None else '',
                    worker_ctx_json,
                    cycle_ctx_json,
                    stack,
                    run_id or ''
                )
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        # Last resort: print to stderr; avoid raising further.
        print(f"[crash_logger] Failed to log crash: {e}", file=sys.stderr)


def get_recent_crashes(db_path: str, worker: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Return recent crash entries for a worker (most recent first).
    """
    rows: List[Dict[str, Any]] = []
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        try:
            cur = conn.execute(
                """
                SELECT cycle_id, node, crashed_at, error_message, error_type, error_code
                FROM crash_logs
                WHERE worker=?
                ORDER BY id DESC
                LIMIT ?
                """,
                (worker, int(max(1, limit)))
            )
            for cycle_id, node, crashed_at, emsg, etype, ecode in cur:
                rows.append({
                    "cycle_id": cycle_id,
                    "node": node,
                    "crashed_at": crashed_at,
                    "error_message": emsg,
                    "error_type": etype,
                    "error_code": ecode,
                })
        finally:
            conn.close()
    except Exception as e:
        print(f"[crash_logger] Failed to read crashes: {e}", file=sys.stderr)
    return rows


def print_crash_report(db_path: str, worker: str, limit: int = 1) -> str:
    """
    Build a human-readable crash report string. Returns the report.
    """
    crashes = get_recent_crashes(db_path, worker, limit)
    if not crashes:
        return "No crashes found."
    lines = ["=== Recent Crashes ==="]
    for c in crashes:
        lines.append(
            f"- [{c.get('crashed_at')}] node={c.get('node')} cycle={c.get('cycle_id')}\n"
            f"  type={c.get('error_type')} code={c.get('error_code')}\n"
            f"  msg={c.get('error_message')}"
        )
    report = "\n".join(lines)
    # Also print to stderr for convenience during CLI usage
    try:
        print(report, file=sys.stderr)
    except Exception:
        pass
    return report
