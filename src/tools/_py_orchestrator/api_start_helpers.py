










from __future__ import annotations
from typing import Dict, Any
from pathlib import Path
from .api_common import PROJECT_ROOT
from .db import set_state_kv


def relpath_from_root(abs_path: str) -> str:
    try:
        p = Path(abs_path).resolve()
        root = PROJECT_ROOT.resolve()
        return p.relative_to(root).as_posix()
    except Exception:
        return abs_path


def resolve_worker_file_safe(worker_name: str, worker_file: str | None) -> str | None:
    """If worker_file is relative or absent, try workers/<name>/process.py.
    Returns a relative path 'workers/<name>/process.py' if found, else None.
    """
    try:
        if worker_file and (worker_file.startswith('workers/') or worker_file.startswith('./workers/')):
            return worker_file
        candidate = Path(PROJECT_ROOT) / 'workers' / worker_name / 'process.py'
        if candidate.is_file():
            return candidate.relative_to(PROJECT_ROOT).as_posix()
    except Exception:
        pass
    return None


def preflight_dry(worker_name: str, db_path: str) -> Dict[str, Any]:
    """Run a dry preflight (no side-effects). Returns an envelope.
    {accepted, issues, preflight} or {accepted:false, code, message}
    Also mirrors error summaries in KV for UI.
    """
    try:
        from .validation_core import validate_full
        pre = validate_full(worker_name, include_preflight=True, persist=False)
        if not pre.get('accepted'):
            try:
                import json as _json
                set_state_kv(db_path, worker_name, 'py.graph_errors', _json.dumps([it.get('message') for it in (pre.get('issues') or []) if (it.get('level')=='error')]) )
            except Exception:
                pass
            return {"accepted": False, "status": "error", "code": "PREFLIGHT_FAILED", "message": "Preflight failed (see issues)", "issues": pre.get('issues') or [], "preflight": pre.get('preflight') or {}}
        return {"accepted": True, "status": "ok", "issues": pre.get('issues') or [], "preflight": pre.get('preflight') or {}}
    except Exception as e:
        try:
            set_state_kv(db_path, worker_name, 'last_error', f"Preflight(dry) exception: {str(e)[:200]}")
        except Exception:
            pass
        return {"accepted": False, "status": "error", "code": "PREFLIGHT_EXCEPTION", "message": str(e)[:300]}
