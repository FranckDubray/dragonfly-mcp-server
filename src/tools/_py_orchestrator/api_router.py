




from __future__ import annotations
from typing import Dict, Any
import importlib

from .api_stop import stop
from .api_debug import debug_control
from .api_list import list_workers
from .api_transforms import list_transforms as list_transforms_op
# from .api_config import config_op  # replaced by dynamic reload below


def route(params: dict) -> Dict[str, Any]:
    op = (params or {}).get('operation', 'start')
    if op == 'start':
        from . import api_start as _st
        try:
            _st = importlib.reload(_st)
        except Exception:
            pass
        return _st.start(params)
    if op == 'stop':
        return stop(params)
    if op == 'status':
        from . import api_status as _s
        try:
            _s = importlib.reload(_s)
        except Exception:
            pass
        return _s.status(params)
    if op == 'debug':
        return debug_control(params)
    if op == 'observe':
        # Passive observation, DO NOT enable step mode
        from . import api_observe as _obs
        try:
            _obs = importlib.reload(_obs)
        except Exception:
            pass
        return _obs.observe_tool(params)
    if op == 'list':
        return list_workers()
    if op == 'graph':
        from . import api_graph as _g
        try:
            _g = importlib.reload(_g)
        except Exception:
            pass
        return _g.graph(params)
    if op == 'validate':
        from . import api_validate as _v
        try:
            _v = importlib.reload(_v)
        except Exception:
            pass
        return _v.validate_worker(params)
    if op == 'transforms':
        return list_transforms_op(params)
    if op == 'config':
        from . import api_config as _cfg
        try:
            _cfg = importlib.reload(_cfg)
        except Exception:
            pass
        return _cfg.config_op(params)
    return {"accepted": False, "status": "error", "message": f"Invalid operation: {op}", "truncated": False}

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
