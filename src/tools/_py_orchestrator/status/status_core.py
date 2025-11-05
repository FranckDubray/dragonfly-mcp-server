"""Core status building logic."""

from __future__ import annotations
from typing import Dict, Any, List
import sqlite3
import json as _json

from ..validators import validate_params
from ..api_spawn import db_path_for_worker
from ..db import get_state_kv


def _recent_steps(db_path: str, worker: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent steps for timeline."""
    try:
        conn = sqlite3.connect(db_path, timeout=2.0)
        try:
            cur = conn.execute(
                "SELECT cycle_id, node, status, started_at, finished_at, duration_ms "
                "FROM job_steps WHERE worker=? ORDER BY rowid DESC LIMIT ?",
                (worker, limit)
            )
            rows = cur.fetchall()
            steps = []
            for row in rows:
                steps.append({
                    'cycle_id': row[0],
                    'node': row[1],
                    'status': row[2],
                    'started_at': row[3],
                    'finished_at': row[4],
                    'duration_ms': int(row[5] or 0),
                })
            return list(reversed(steps))
        finally:
            conn.close()
    except Exception:
        return []


def _llm_usage_from_kv(db_path: str, worker: str) -> Dict[str, Any]:
    """Extract LLM usage metrics from KV."""
    try:
        total = int(get_state_kv(db_path, worker, 'usage.llm.total_tokens') or 0)
        input_tok = int(get_state_kv(db_path, worker, 'usage.llm.input_tokens') or 0)
        output_tok = int(get_state_kv(db_path, worker, 'usage.llm.output_tokens') or 0)
        by_model_raw = get_state_kv(db_path, worker, 'usage.llm.by_model') or '{}'
        try:
            by_model = _json.loads(by_model_raw)
        except Exception:
            by_model = {}
        return {
            'total_tokens': total,
            'input_tokens': input_tok,
            'output_tokens': output_tok,
            'by_model': by_model if isinstance(by_model, dict) else {},
        }
    except Exception:
        return {'total_tokens': 0, 'input_tokens': 0, 'output_tokens': 0, 'by_model': {}}


def build_status(params: dict) -> dict:
    """Build status response for a worker."""
    p = validate_params({**params, 'operation': 'status'})
    wn = p['worker_name']
    db_path = db_path_for_worker(wn)
    
    # Basic KV state
    phase = get_state_kv(db_path, wn, 'phase') or 'unknown'
    pid_str = get_state_kv(db_path, wn, 'pid') or ''
    pid = None
    try:
        if pid_str:
            pid = int(pid_str)
    except Exception:
        pass
    
    heartbeat = get_state_kv(db_path, wn, 'heartbeat') or ''
    last_error = get_state_kv(db_path, wn, 'last_error') or ''
    process_uid = get_state_kv(db_path, wn, 'process_uid') or ''
    
    # Metrics
    include_metrics = bool((params or {}).get('include_metrics'))
    metrics = {}
    llm_usage = {}
    if include_metrics:
        llm_usage = _llm_usage_from_kv(db_path, wn)
        metrics = {
            'llm_usage': llm_usage,
        }
    
    # Recent steps (timeline)
    recent_steps = _recent_steps(db_path, wn, limit=10)
    
    # Summary (if available)
    summary = get_state_kv(db_path, wn, 'py.last_summary') or ''
    
    # Debug state (if enabled)
    debug_enabled = (get_state_kv(db_path, wn, 'debug.enabled') == 'true')
    debug_info = {}
    if debug_enabled:
        debug_info = {
            'enabled': True,
            'mode': get_state_kv(db_path, wn, 'debug.mode') or '',
            'paused_at': get_state_kv(db_path, wn, 'debug.paused_at') or '',
            'next_node': get_state_kv(db_path, wn, 'debug.next_node') or '',
        }
    
    out = {
        'accepted': True,
        'status': phase,
        'worker_name': wn,
        'pid': pid,
        'heartbeat': heartbeat,
        'last_error': last_error if last_error else None,
        'process_uid': process_uid,
        'db_path': db_path,
        'summary': summary if summary else None,
        'recent_steps': recent_steps,
        'metrics': metrics,
        'llm_usage': llm_usage,
        'debug': debug_info if debug_enabled else None,
        'truncated': False,
    }
    
    return out
