

from typing import Dict, Any
from .api_start import start
from .api_stop import stop
# from .api_status import status  # switch to lazy import
from .api_debug import debug_control
from .api_list import list_workers
# from .api_graph import graph as graph_op  # switch to lazy import
# from .api_validate import validate_worker as validate_op  # switch to lazy import
from .api_transforms import list_transforms as list_transforms_op

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
        return {"accepted": False, "status": "error", "message": f"Invalid operation: {op}", "truncated": False}
    except ValueError as e:
        return {"accepted": False, "status": "error", "message": str(e)[:400], "truncated": False}
    except Exception as e:
        return {"accepted": False, "status": "error", "message": f"Unexpected error: {str(e)[:350]}", "truncated": False}
