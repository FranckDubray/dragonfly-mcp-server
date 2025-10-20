# API errors helpers - Error reporting and debug status (<4KB)

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict

from .db import get_state_kv, get_phase


def check_heartbeat_fresh(db_path: str, worker: str, ttl_seconds: int = 90) -> bool:
    """
    Check if worker heartbeat is fresh (within TTL).
    
    Args:
        db_path: DB path
        worker: Worker name
        ttl_seconds: TTL in seconds (default 90s)
    
    Returns:
        True if heartbeat is recent
    """
    hb = get_state_kv(db_path, worker, 'heartbeat')
    if not hb:
        return False
    try:
        hb_dt = datetime.fromisoformat(hb.replace(' ', 'T'))
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        return (now - hb_dt).total_seconds() < ttl_seconds
    except Exception:
        return False


def compact_errors_for_status(db_path: str, worker_name: str) -> Dict[str, Any]:
    """
    Extract recent errors and crashes for status response.
    
    Returns:
        Dict with 'errors' and/or 'crash' keys
    """
    info: Dict[str, Any] = {}
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT cycle_id FROM job_steps WHERE worker=? ORDER BY id DESC LIMIT 1", (worker_name,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return info
        cycle_id = row[0]
        cur.execute(
            """
            SELECT node, started_at, finished_at, duration_ms, details_json
            FROM job_steps
            WHERE worker=? AND cycle_id=? AND status='failed'
            ORDER BY id DESC LIMIT 10
            """,
            (worker_name, cycle_id)
        )
        failed_rows = cur.fetchall()
        errors = []
        for n, s_at, f_at, dur, dj in failed_rows:
            msg = code = category = None
            attempts = None
            try:
                d = json.loads(dj) if dj else {}
                err = d.get('error') or {}
                msg = (err.get('message') or '')[:200]
                code = err.get('code')
                category = err.get('category')
                attempts = d.get('attempts')
            except Exception:
                pass
            errors.append({'node': n, 'started_at': s_at, 'finished_at': f_at, 'duration_ms': dur,
                           'message': msg, 'code': code, 'category': category, 'attempts': attempts})
        if errors:
            info['errors'] = errors
        cur.execute(
            """
            SELECT node, crashed_at, error_message, error_type, error_code, stack_trace
            FROM crash_logs
            WHERE worker=? AND cycle_id=?
            ORDER BY id DESC LIMIT 1
            """,
            (worker_name, cycle_id)
        )
        c = cur.fetchone()
        if c:
            node, crashed_at, emsg, etype, ecode, trace = c
            info['crash'] = {'node': node, 'crashed_at': crashed_at,
                             'error_message': (emsg or '')[:300], 'error_type': etype,
                             'error_code': ecode, 'trace': (trace or '')[:400]}
        conn.close()
    except Exception:
        pass
    return info


def debug_status_block(db_path: str, worker_name: str) -> Dict[str, Any]:
    """
    Build debug status block for status response.
    
    Returns:
        Dict with 'debug' key if debug is enabled, empty dict otherwise
    """
    blk: Dict[str, Any] = {}
    try:
        enabled = get_state_kv(db_path, worker_name, 'debug.enabled') == 'true'
        if not enabled:
            return {}
        mode = get_state_kv(db_path, worker_name, 'debug.mode') or 'step'
        paused_at = get_state_kv(db_path, worker_name, 'debug.paused_at') or ''
        next_node = get_state_kv(db_path, worker_name, 'debug.next_node') or ''
        previous_node = get_state_kv(db_path, worker_name, 'debug.previous_node') or ''
        cycle_id = get_state_kv(db_path, worker_name, 'debug.cycle_id') or ''
        breaks = get_state_kv(db_path, worker_name, 'debug.breakpoints') or '[]'
        import json as _j
        blk = {
            'debug': {
                'enabled': True,
                'mode': mode,
                'paused': get_phase(db_path, worker_name) == 'debug_paused',
                'paused_at': paused_at,
                'previous_node': previous_node,
                'next_node': next_node,
                'cycle_id': cycle_id,
                'breakpoints_count': len(_j.loads(breaks))
            }
        }
    except Exception:
        return {}
    return blk
