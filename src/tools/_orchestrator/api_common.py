# Shared helpers and constants for orchestrator tool API (kept <7KB)

import json
import hashlib
import subprocess
import sys
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# DB/state helpers
from .db import get_state_kv, set_state_kv, get_phase, set_phase, heartbeat

# Optional JSON schema
try:
    from jsonschema import validate as validate_schema, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    ValidationError = None

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SQLITE_DIR = PROJECT_ROOT / 'sqlite3'
LOG_DIR = PROJECT_ROOT / 'logs'

SCHEMA_PATH = Path(__file__).parent / 'schemas' / 'process.schema.json'
PROCESS_SCHEMA = None
if SCHEMA_PATH.exists():
    try:
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            PROCESS_SCHEMA = json.load(f)
    except Exception:
        PROCESS_SCHEMA = None


def compute_process_uid(worker_file_resolved: str) -> str:
    with open(worker_file_resolved, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:12]


def db_path_for_worker(worker_name: str) -> str:
    SQLITE_DIR.mkdir(parents=True, exist_ok=True)
    return str(SQLITE_DIR / f"worker_{worker_name}.db")


def check_heartbeat_fresh(db_path: str, worker: str, ttl_seconds: int = 90) -> bool:
    hb = get_state_kv(db_path, worker, 'heartbeat')
    if not hb:
        return False
    try:
        hb_dt = datetime.fromisoformat(hb.replace(' ', 'T'))
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        return (now - hb_dt).total_seconds() < ttl_seconds
    except Exception:
        return False


def spawn_runner(db_path: str, worker_name: str) -> int:
    cmd = [sys.executable, '-m', 'src.tools._orchestrator.runner', db_path]
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"worker_{worker_name}.log"
    log_fh = open(log_path, 'ab', buffering=0)
    if os.name == 'nt':
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        proc = subprocess.Popen(cmd, cwd=str(PROJECT_ROOT), creationflags=flags,
                                stdin=subprocess.DEVNULL, stdout=log_fh, stderr=log_fh)
    else:
        proc = subprocess.Popen(cmd, cwd=str(PROJECT_ROOT), start_new_session=True,
                                stdin=subprocess.DEVNULL, stdout=log_fh, stderr=log_fh)
    return proc.pid


def validate_process_schema(process_data: dict) -> Optional[Dict[str, Any]]:
    if not JSONSCHEMA_AVAILABLE or not PROCESS_SCHEMA:
        return None
    try:
        validate_schema(instance=process_data, schema=PROCESS_SCHEMA)
    except ValidationError as e:
        return {
            "accepted": False,
            "status": "failed",
            "message": f"Invalid process schema: {e.message[:250]}",
            "validation_path": list(e.absolute_path) if e.absolute_path else [],
            "schema_path": list(e.absolute_schema_path) if e.absolute_schema_path else [],
            "truncated": False
        }
    return None


def validate_process_logic(process_data: dict) -> Optional[str]:
    # Guard: no top-level $import (must import under graph)
    if "$import" in process_data:
        return "Top-level $import not allowed (use graph.$import to preserve worker_ctx)"

    if not isinstance(process_data.get('worker_ctx'), dict):
        return "worker_ctx must be an object (and must include db_name)"
    if not process_data['worker_ctx'].get('db_name'):
        return "worker_ctx.db_name required (single data DB per worker)"

    graph = process_data.get('graph', {})
    if not isinstance(graph, dict) or not graph:
        return "graph must be an object (import under graph if splitting)"

    nodes = graph.get('nodes', [])
    edges = graph.get('edges', [])
    if not nodes:
        return "Graph must have at least one node"

    node_names = {n['name'] for n in nodes}
    if len(node_names) != len(nodes):
        names_list = [n['name'] for n in nodes]
        duplicates = [name for name in names_list if names_list.count(name) > 1]
        return f"Duplicate node names: {', '.join(set(duplicates))}"

    start_nodes = [n for n in nodes if n.get('type') == 'start']
    if len(start_nodes) == 0:
        return "No START node found (type='start' required)"
    if len(start_nodes) > 1:
        return f"Multiple START nodes found: {', '.join(n['name'] for n in start_nodes)}"

    for i, edge in enumerate(edges):
        from_node = edge.get('from')
        to_node = edge.get('to')
        if from_node not in node_names:
            return f"Edge #{i}: 'from' references unknown node '{from_node}'"
        if to_node not in node_names:
            return f"Edge #{i}: 'to' references unknown node '{to_node}'"

    edge_signatures = [(e.get('from'), e.get('when', 'always')) for e in edges]
    if len(edge_signatures) != len(set(edge_signatures)):
        duplicates = [sig for sig in edge_signatures if edge_signatures.count(sig) > 1]
        return f"Duplicate edges detected: {duplicates[:3]}"

    # Optional: basic call_llm sanity (presence of messages)
    for n in nodes:
        if n.get('type') == 'io' and n.get('handler') == 'http_tool':
            inp = n.get('inputs', {}) or {}
            if inp.get('tool') == 'call_llm':
                # messages must exist after resolution; we only check presence here
                if 'messages' not in inp:
                    return f"LLM node '{n.get('name')}' missing 'messages'"

    return None


def compact_errors_for_status(db_path: str, worker_name: str) -> Dict[str, Any]:
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
    blk: Dict[str, Any] = {}
    try:
        enabled = get_state_kv(db_path, worker_name, 'debug.enabled') == 'true'
        if not enabled:
            return {}
        mode = get_state_kv(db_path, worker_name, 'debug.mode') or 'step'
        paused_at = get_state_kv(db_path, worker_name, 'debug.paused_at') or ''
        next_node = get_state_kv(db_path, worker_name, 'debug.next_node') or ''
        cycle_id = get_state_kv(db_path, worker_name, 'debug.cycle_id') or ''
        breaks = get_state_kv(db_path, worker_name, 'debug.breakpoints') or '[]'
        import json as _j
        blk = {
            'debug': {
                'enabled': True,
                'mode': mode,
                'paused': get_phase(db_path, worker_name) == 'debug_paused',
                'paused_at': paused_at,
                'next_node': next_node,
                'cycle_id': cycle_id,
                'breakpoints_count': len(_j.loads(breaks))
            }
        }
    except Exception:
        return {}
    return blk
