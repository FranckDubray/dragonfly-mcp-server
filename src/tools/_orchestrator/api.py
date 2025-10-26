


















# Orchestrator tool API (router) — split into small modules (<7KB)

from typing import Dict, Any

from .api_start import start
from .api_stop import stop
from .api_status_debug import status, debug_control
from .api_list import list_workers


def start_or_control(params: dict) -> Dict[str, Any]:
    op = (params or {}).get('operation', 'start')
    try:
        if op == 'start':
            return start(params)
        elif op == 'stop':
            return stop(params)
        elif op == 'status':
            return status(params)
        elif op == 'debug':
            return debug_control(params)
        elif op == 'list':
            return list_workers()
        else:
            return {"accepted": False, "status": "error", "message": f"Invalid operation: {op}", "truncated": False}
    except ValueError as e:
        return {"accepted": False, "status": "error", "message": str(e)[:400], "truncated": False}
    except Exception as e:
        return {"accepted": False, "status": "error", "message": f"Unexpected error: {str(e)[:350]}", "truncated": False}
