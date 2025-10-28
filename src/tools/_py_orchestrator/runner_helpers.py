
from __future__ import annotations
from typing import Dict, Any
from .db import get_state_kv


def is_canceled(db_path: str, worker: str) -> bool:
    try:
        v = get_state_kv(db_path, worker, 'cancel') or ''
        return str(v).strip().lower() == 'true'
    except Exception:
        return False


def is_debug_enabled(db_path: str, worker: str) -> bool:
    try:
        return (get_state_kv(db_path, worker, 'debug.enabled') == 'true')
    except Exception:
        return False


def get_debug_state(db_path: str, worker: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    try:
        keys = ['enabled','mode','pause_request','until','breakpoints','command']
        for k in keys:
            out[k] = get_state_kv(db_path, worker, f'debug.{k}') or ''
        # Optionally decode breakpoints if JSON stored
        try:
            import json
            b = out.get('breakpoints')
            if b and isinstance(b, str) and b.strip().startswith('['):
                out['breakpoints'] = json.loads(b)
        except Exception:
            pass
        return out
    except Exception:
        return {}
