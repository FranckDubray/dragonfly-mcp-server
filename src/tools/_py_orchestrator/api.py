













from typing import Dict, Any
from .api_start import start
from .api_stop import stop
# from .api_status import status  # switch to lazy import
from .api_debug import debug_control
from .api_list import list_workers
# from .api_graph import graph as graph_op  # switch to lazy import
# from .api_validate import validate_worker as validate_op  # switch to lazy import
from .api_transforms import list_transforms as list_transforms_op
from .api_spawn import db_path_for_worker
from .db import get_state_kv, set_state_kv
from .validators import PY_WORKERS_DIR
import importlib
import json
import pathlib
import pprint
import re


def _persist_config_file(worker_name: str, key: str, value: Any) -> bool:
    """Best-effort: update workers/<worker>/config.py CONFIG[key] = value.
    - Safely load current CONFIG from the module by executing it in a sandbox dict.
    - Update CONFIG in-memory.
    - Replace the CONFIG block in file (regex) or append if not found.
    Returns True on success, False otherwise.
    """
    try:
        cfg_path = pathlib.Path(PY_WORKERS_DIR) / worker_name / 'config.py'
        if not cfg_path.is_file():
            return False
        src = cfg_path.read_text(encoding='utf-8')
        # Execute module to get CONFIG-like dict
        ns: Dict[str, Any] = {}
        try:
            exec(compile(src, str(cfg_path), 'exec'), {}, ns)
        except Exception:
            # If execution fails, fallback to empty CONFIG
            pass
        # Pick first available dict
        cfg = None
        for k in ('CONFIG', 'WORKER_CONFIG', 'config'):
            if isinstance(ns.get(k), dict):
                cfg = dict(ns.get(k))
                break
        if cfg is None:
            cfg = {}
        cfg[key] = value
        # Pretty Python repr (preserve Python booleans/None)
        cfg_repr = pprint.pformat(cfg, width=100, sort_dicts=False)
        new_block = f"CONFIG = {cfg_repr}\n\n"
        # Try to replace existing CONFIG = { ... }
        pattern = re.compile(r"CONFIG\s*=\s*\{[\s\S]*?\}\s*\n", flags=re.MULTILINE)
        if pattern.search(src):
            new_src = pattern.sub(new_block, src, count=1)
        else:
            # Append at end
            new_src = src.rstrip() + "\n\n" + new_block
        cfg_path.write_text(new_src, encoding='utf-8')
        return True
    except Exception:
        return False


def start_or_control(params: dict) -> Dict[str, Any]:
    op = (params or {}).get('operation', 'start')
    try:
        if op == 'start':
            return start(params)
        if op == 'stop':
            return stop(params)
        if op == 'status':
            # Lazy import to pick up code changes without process restart
            from . import api_status as _s
            try:
                _s = importlib.reload(_s)
            except Exception:
                pass
            return _s.status(params)
        if op == 'debug':
            return debug_control(params)
        if op == 'list':
            return list_workers()
        if op == 'graph':
            from . import api_graph as _g
            return _g.graph(params)
        if op == 'validate':
            from . import api_validate as _v
            return _v.validate_worker(params)
        if op == 'transforms':
            return list_transforms_op(params)
        if op == 'config':
            # Return and/or update current worker metadata + optional docs (from KV)
            wn = (params or {}).get('worker_name')
            if not wn:
                return {"accepted": False, "status": "error", "message": "worker_name required", "truncated": False}
            dbp = db_path_for_worker(wn)
            # Update path (optional)
            set_req = (params or {}).get('set') or {}
            changed = False
            file_persisted = False
            if isinstance(set_req, dict) and set_req.get('key') is not None:
                k = str(set_req.get('key'))
                v = set_req.get('value')
                try:
                    raw_md = get_state_kv(dbp, wn, 'py.process_metadata') or '{}'
                    md = json.loads(raw_md)
                except Exception:
                    md = {}
                # shallow update only (ctx vars)
                md[k] = v
                try:
                    set_state_kv(dbp, wn, 'py.process_metadata', json.dumps(md))
                    changed = True
                except Exception:
                    pass
                # Best-effort: persist into workers/<wn>/config.py CONFIG
                file_persisted = _persist_config_file(wn, k, v)
            # Read path
            try:
                raw_md = get_state_kv(dbp, wn, 'py.process_metadata') or '{}'
                md = json.loads(raw_md)
            except Exception:
                md = {}
            try:
                raw_docs = get_state_kv(dbp, wn, 'py.process_config_docs') or '{}'
                docs = json.loads(raw_docs)
            except Exception:
                docs = {}
            return {"accepted": True, "status": "ok", "worker_name": wn, "metadata": md, "docs": docs, "changed": changed, "file_persisted": bool(file_persisted), "truncated": False}
        return {"accepted": False, "status": "error", "message": f"Invalid operation: {op}", "truncated": False}
    except ValueError as e:
        return {"accepted": False, "status": "error", "message": str(e)[:400], "truncated": False}
    except Exception as e:
        return {"accepted": False, "status": "error", "message": f"Unexpected error: {str(e)[:350]}", "truncated": False}

 
 
 
 
 
 
 
 
 
 
 
