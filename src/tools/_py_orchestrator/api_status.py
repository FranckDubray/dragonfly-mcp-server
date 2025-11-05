"""Status API with comprehensive error details."""

from .status.status_core import build_status as _build_status
from .status.error_details import collect_error_details
from pathlib import Path
from .api_common import PROJECT_ROOT
from .api_spawn import db_path_for_worker


def _relpath_from_root(p: str) -> str:
    try:
        if not p:
            return p
        abs_p = Path(p).resolve()
        root = PROJECT_ROOT.resolve()
        return abs_p.relative_to(root).as_posix()
    except Exception:
        return p


def status(params: dict) -> dict:
    out = _build_status(params)
    
    # Normalize paths to be relative to project root (db_path, log_path if present)
    try:
        if isinstance(out, dict):
            if 'db_path' in out:
                out['db_path'] = _relpath_from_root(out.get('db_path'))
            if 'log_path' in out:
                out['log_path'] = _relpath_from_root(out.get('log_path'))
    except Exception:
        pass
    
    # LLM usage metrics
    try:
        m = out.get('metrics') or {}
        # llm_usage peut être soit top-level, soit imbriqué dans metrics
        llm = out.get('llm_usage') or (m.get('llm_usage') if isinstance(m, dict) else {}) or {}
        if isinstance(m, dict) and isinstance(llm, dict) and llm:
            # Refléter llm_usage dans metrics pour cohérence UI
            m['llm_tokens'] = {
                'total': llm.get('total_tokens', 0),
                'input': llm.get('input_tokens', 0),
                'output': llm.get('output_tokens', 0),
            }
            m['token_llm'] = llm.get('by_model') or {}
            out['metrics'] = m
    except Exception:
        pass
    
    # NEW: surface preflight warnings/errors if any (KV persisted)
    try:
        wn = (params or {}).get('worker_name')
        if wn:
            from .db import get_state_kv
            dbp = db_path_for_worker(wn)
            import json
            warn_raw = get_state_kv(dbp, wn, 'py.graph_warnings') or ''
            err_raw = get_state_kv(dbp, wn, 'py.graph_errors') or ''
            if warn_raw:
                try:
                    out['preflight_warnings'] = json.loads(warn_raw)
                except Exception:
                    out['preflight_warnings'] = [warn_raw]
            if err_raw:
                try:
                    out['preflight_errors'] = json.loads(err_raw)
                except Exception:
                    out['preflight_errors'] = [err_raw]
    except Exception:
        pass
    
    # NEW: Comprehensive error details when worker is in error state
    try:
        wn = (params or {}).get('worker_name')
        if wn and isinstance(out, dict):
            phase = out.get('status') or out.get('phase') or ''
            if phase in {'failed', 'canceled', 'error'}:
                dbp = db_path_for_worker(wn)
                error_details = collect_error_details(dbp, wn)
                if error_details:
                    out['error_details'] = error_details
    except Exception:
        pass
    
    return out
