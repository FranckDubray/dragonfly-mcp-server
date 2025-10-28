























































import json
from pathlib import Path
from typing import Any, Dict

from ..validators import validate_params
from ..api_spawn import db_path_for_worker
from ..db import get_phase
from .kv_utils import read_kv
from .metrics import metrics_current_run, recent_steps, crash_packet, structure_counts, split_node, progress_for_node


def _read_llm_usage(db_path: str, worker_name: str) -> Dict[str, Any]:
    try:
        tot = read_kv(db_path, worker_name, 'usage.llm.total_tokens') or '0'
        inp = read_kv(db_path, worker_name, 'usage.llm.input_tokens') or '0'
        out = read_kv(db_path, worker_name, 'usage.llm.output_tokens') or '0'
        bym_raw = read_kv(db_path, worker_name, 'usage.llm.by_model') or '{}'
        try:
            bym = json.loads(bym_raw)
            if not isinstance(bym, dict):
                bym = {}
        except Exception:
            bym = {}
        def _toi(s: str) -> int:
            try:
                return int(s)
            except Exception:
                try:
                    return int(float(s))
                except Exception:
                    return 0
        return {
            'total_tokens': _toi(tot),
            'input_tokens': _toi(inp),
            'output_tokens': _toi(out),
            'by_model': bym,
        }
    except Exception:
        return {}


def build_status(params: dict) -> dict:
    p = validate_params({**params, 'operation': 'status'})
    worker_name = p['worker_name']
    db_path = db_path_for_worker(worker_name)
    if not Path(db_path).exists():
        return {"accepted": True, "status": "unknown", "worker_name": worker_name,
                "message": "No DB found (worker never started or DB deleted)", "truncated": False}

    try:
        phase = get_phase(db_path, worker_name) or 'unknown'
    except Exception:
        phase = 'unknown'
    pid_str = read_kv(db_path, worker_name, 'pid')
    hb = read_kv(db_path, worker_name, 'heartbeat')
    process_uid = read_kv(db_path, worker_name, 'process_uid')
    run_id = read_kv(db_path, worker_name, 'run_id')

    result: Dict[str, Any] = {
        "accepted": True,
        "status": phase,
        "worker_name": worker_name,
        "pid": int(pid_str) if pid_str and pid_str.isdigit() else None,
        "heartbeat": hb,
        "db_path": db_path,
        "truncated": False,
    }
    if process_uid:
        result['process_uid'] = process_uid
    if run_id:
        result['run_id'] = run_id

    # Py-specific block (metadata + last_error, last_call/preview, crash)
    try:
        meta_raw = read_kv(db_path, worker_name, 'py.process_metadata')
        metadata = json.loads(meta_raw) if meta_raw else {}
        last_summary = read_kv(db_path, worker_name, 'py.last_summary')
        last_error = read_kv(db_path, worker_name, 'last_error')
        phase_trace = read_kv(db_path, worker_name, 'debug.phase_trace')
        py_block = {"metadata": metadata}
        if last_summary:
            py_block["summary"] = last_summary
        if last_error:
            py_block["last_error"] = last_error
        if phase_trace:
            py_block["debug_trace"] = phase_trace
        # recent last_call / last_result_preview (from latest job_steps)
        try:
            recents = recent_steps(db_path, worker_name, limit=1)
            if recents:
                r0 = recents[0]
                if 'call' in r0:
                    py_block['last_call'] = r0['call']
                if 'last_result_preview' in r0:
                    py_block['last_result_preview'] = r0['last_result_preview']
        except Exception:
            pass
        # Fallback to KV previews if recent_steps has nothing
        try:
            kv_call = read_kv(db_path, worker_name, 'py.last_call')
            kv_res = read_kv(db_path, worker_name, 'py.last_result_preview')
            if kv_call and 'last_call' not in py_block:
                py_block['last_call'] = kv_call
            if kv_res and 'last_result_preview' not in py_block:
                py_block['last_result_preview'] = kv_res
        except Exception:
            pass
        # Crash packet
        cp = crash_packet(db_path, worker_name)
        if cp:
            py_block['crash_packet'] = cp
        result['py'] = py_block
    except Exception:
        pass

    # Debug block — never empty: include nodes from KV
    dbg_enabled = (read_kv(db_path, worker_name, 'debug.enabled') == 'true')
    dbg_mode = read_kv(db_path, worker_name, 'debug.mode') or ''
    paused_at = read_kv(db_path, worker_name, 'debug.paused_at') or ''
    next_node = read_kv(db_path, worker_name, 'debug.next_node') or ''
    prev_node = read_kv(db_path, worker_name, 'debug.previous_node') or ''
    exec_node = read_kv(db_path, worker_name, 'debug.executing_node') or ''
    cycle_id = read_kv(db_path, worker_name, 'debug.cycle_id') or ''
    paused_effective = bool(paused_at) or bool(next_node)
    if dbg_enabled and paused_effective:
        result['status'] = 'debug_paused'
    result['debug'] = {
        'enabled': dbg_enabled,
        'mode': dbg_mode,
        'paused': paused_effective,
        'paused_at': paused_at or next_node or '',
        'current_node': exec_node or (paused_at or next_node or ''),
        'previous_node': prev_node,
        'next_node': next_node,
        'cycle_id': cycle_id,
        'breakpoints_count': 0,
    }

    # Optional metrics
    metrics_param = (params or {}).get('metrics') or {}
    include_metrics = bool(params.get('include_metrics')) or bool(metrics_param.get('include'))
    if include_metrics:
        m = metrics_current_run(db_path, worker_name)
        try:
            m['structure'] = structure_counts(worker_name)
            # step-by-step navigation helpers
            cur = exec_node or paused_at or read_kv(db_path, worker_name, 'debug.executing_node') or ''
            nxt = next_node
            if not cur and nxt:
                cur = nxt
            m['structure']['current_node'] = cur
            m['structure']['next_node'] = nxt
            m['structure']['current'] = split_node(cur) if cur else {"subgraph": "", "step": "", "full": ""}
            m['structure']['next'] = split_node(nxt) if nxt else {"subgraph": "", "step": "", "full": ""}
            # progress within current subgraph (topological order)
            m['structure']['progress'] = progress_for_node(worker_name, cur)
        except Exception:
            pass
        # LLM usage accumulation (from KV, no DB query needed)
        try:
            m['llm_usage'] = _read_llm_usage(db_path, worker_name)
        except Exception:
            pass
        result['metrics'] = m

    # Recent steps preview
    try:
        result['recent_steps'] = recent_steps(db_path, worker_name, limit=5)
    except Exception:
        pass

    return result
