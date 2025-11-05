"""Collect comprehensive error context for failed workers."""

from __future__ import annotations
from typing import Dict, Any, List
import sqlite3
import json as _json

from ..db import get_state_kv


def collect_error_details(db_path: str, worker: str) -> Dict[str, Any]:
    """
    Collect all available error context for a failed worker.
    Returns a comprehensive error_details dict suitable for UI display.
    """
    details: Dict[str, Any] = {}
    
    # Phase and basic error
    try:
        phase = get_state_kv(db_path, worker, 'phase') or ''
        details['phase'] = phase
        details['is_error'] = phase in {'failed', 'canceled'}
    except Exception:
        details['phase'] = 'unknown'
        details['is_error'] = False
    
    # Last error message
    try:
        last_error = get_state_kv(db_path, worker, 'last_error') or ''
        if last_error:
            details['last_error'] = last_error
    except Exception:
        pass
    
    # Last call context (what was being executed)
    try:
        last_call = get_state_kv(db_path, worker, 'py.last_call') or ''
        if last_call:
            try:
                # Try to parse as JSON if it looks like JSON
                if last_call.strip().startswith('{'):
                    details['last_call'] = _json.loads(last_call)
                else:
                    details['last_call'] = last_call
            except Exception:
                details['last_call'] = last_call
    except Exception:
        pass
    
    # Last result preview
    try:
        last_result = get_state_kv(db_path, worker, 'py.last_result_preview') or ''
        if last_result:
            details['last_result_preview'] = last_result
    except Exception:
        pass
    
    # Debug context if available
    try:
        paused_at = get_state_kv(db_path, worker, 'debug.paused_at') or ''
        executing = get_state_kv(db_path, worker, 'debug.executing_node') or ''
        previous = get_state_kv(db_path, worker, 'debug.previous_node') or ''
        if paused_at or executing or previous:
            details['debug_context'] = {
                'paused_at': paused_at,
                'executing_node': executing,
                'previous_node': previous,
            }
    except Exception:
        pass
    
    # Recent crash logs (last 3)
    try:
        conn = sqlite3.connect(db_path, timeout=2.0)
        try:
            # Check if crash_logs table exists
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='crash_logs'"
            )
            if cur.fetchone():
                cur = conn.execute(
                    "SELECT timestamp, cycle_id, node, error_type, error_message, traceback, "
                    "worker_context, cycle_context FROM crash_logs "
                    "WHERE worker=? ORDER BY id DESC LIMIT 3",
                    (worker,)
                )
                rows = cur.fetchall()
                if rows:
                    crashes: List[Dict[str, Any]] = []
                    for row in rows:
                        crash = {
                            'timestamp': row[0],
                            'cycle_id': row[1],
                            'node': row[2],
                            'error_type': row[3],
                            'error_message': row[4],
                            'traceback': row[5],
                        }
                        # Parse JSON contexts if available
                        try:
                            if row[6]:
                                crash['worker_context'] = _json.loads(row[6])
                        except Exception:
                            pass
                        try:
                            if row[7]:
                                crash['cycle_context'] = _json.loads(row[7])
                        except Exception:
                            pass
                        crashes.append(crash)
                    details['recent_crashes'] = crashes
        finally:
            conn.close()
    except Exception:
        pass
    
    # Preflight errors/warnings (if any)
    try:
        graph_errors = get_state_kv(db_path, worker, 'py.graph_errors') or ''
        if graph_errors:
            try:
                details['graph_errors'] = _json.loads(graph_errors)
            except Exception:
                details['graph_errors'] = [graph_errors]
    except Exception:
        pass
    
    try:
        graph_warnings = get_state_kv(db_path, worker, 'py.graph_warnings') or ''
        if graph_warnings:
            try:
                details['graph_warnings'] = _json.loads(graph_warnings)
            except Exception:
                details['graph_warnings'] = [graph_warnings]
    except Exception:
        pass
    
    # Last failed step from job_steps
    try:
        conn = sqlite3.connect(db_path, timeout=2.0)
        try:
            cur = conn.execute(
                "SELECT cycle_id, node, status, started_at, finished_at, details_json "
                "FROM job_steps WHERE worker=? AND status='failed' "
                "ORDER BY rowid DESC LIMIT 1",
                (worker,)
            )
            row = cur.fetchone()
            if row:
                failed_step = {
                    'cycle_id': row[0],
                    'node': row[1],
                    'status': row[2],
                    'started_at': row[3],
                    'finished_at': row[4],
                }
                # Parse details_json if available
                try:
                    if row[5]:
                        step_details = _json.loads(row[5])
                        if isinstance(step_details, dict):
                            failed_step['details'] = step_details
                except Exception:
                    pass
                details['last_failed_step'] = failed_step
        finally:
            conn.close()
    except Exception:
        pass
    
    # Worker metadata (config that was active)
    try:
        metadata = get_state_kv(db_path, worker, 'py.process_metadata') or ''
        if metadata:
            try:
                md = _json.loads(metadata)
                if isinstance(md, dict):
                    # Only include non-sensitive, useful fields
                    safe_md = {}
                    for k in ['db_file', 'llm_model', 'http_timeout_sec', 'quality_threshold', 'max_retries']:
                        if k in md:
                            safe_md[k] = md[k]
                    if safe_md:
                        details['worker_metadata'] = safe_md
            except Exception:
                pass
    except Exception:
        pass
    
    # Summary of what went wrong (human-readable)
    try:
        summary_parts: List[str] = []
        if details.get('phase') == 'failed':
            summary_parts.append("❌ Worker failed")
        elif details.get('phase') == 'canceled':
            summary_parts.append("⚠️ Worker was canceled")
        
        if details.get('last_error'):
            summary_parts.append(f"Error: {details['last_error'][:200]}")
        
        if details.get('last_failed_step'):
            node = details['last_failed_step'].get('node', '')
            summary_parts.append(f"Failed at step: {node}")
        
        if details.get('last_call'):
            call = details['last_call']
            if isinstance(call, dict):
                kind = call.get('kind', '')
                name = call.get('name', '')
                if kind and name:
                    summary_parts.append(f"Last call: {kind}({name})")
        
        if summary_parts:
            details['summary'] = '\n'.join(summary_parts)
    except Exception:
        pass
    
    return details
