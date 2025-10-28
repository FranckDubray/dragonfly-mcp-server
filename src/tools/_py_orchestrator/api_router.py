
from __future__ import annotations
from typing import Dict, Any
import importlib


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
        from . import api_stop as _sp
        try:
            _sp = importlib.reload(_sp)
        except Exception:
            pass
        return _sp.stop(params)
    if op == 'status':
        from . import api_status as _s
        try:
            _s = importlib.reload(_s)
        except Exception:
            pass
        return _s.status(params)
    if op == 'debug':
        from . import api_debug as _d
        try:
            _d = importlib.reload(_d)
        except Exception:
            pass
        return _d.debug_control(params)
    if op == 'observe':
        # Passive observation, DO NOT enable debug nor issue step/continue
        from . import api_observe as _obs
        try:
            _obs = importlib.reload(_obs)
        except Exception:
            pass
        return _obs.observe_tool(params)
    if op == 'list':
        from . import api_list as _lst
        try:
            _lst = importlib.reload(_lst)
        except Exception:
            pass
        return _lst.list_workers()
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
        from . import api_transforms as _t
        try:
            _t = importlib.reload(_t)
        except Exception:
            pass
        return _t.list_transforms(params)
    if op == 'config':
        from . import api_config as _cfg
        try:
            _cfg = importlib.reload(_cfg)
        except Exception:
            pass
        return _cfg.config_op(params)
    return {"accepted": False, "status": "error", "message": f"Invalid operation: {op}", "truncated": False}
