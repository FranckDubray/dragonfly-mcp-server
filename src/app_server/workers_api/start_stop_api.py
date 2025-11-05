






















from __future__ import annotations
from typing import Dict, Any, Optional

async def start_worker(
    worker_name: Optional[str] = None,
    worker_file: Optional[str] = None,
    hot_reload: bool = True,
    debug_enable: bool = False,
    debug_pause_at_start: bool = False,
    leader_name: Optional[str] = None,
    new_worker: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Facade /workers/api/start
    - Backward compatible with legacy (worker_name + worker_file)
    - Official support for new_worker {first_name, template} which delegates derivation
      to py_orchestrator.start (it will create identity and derive worker_name/worker_file).
    """
    from src.tools._py_orchestrator.api_router import route as py_route
    dbg: Dict[str, Any] = {}
    if debug_enable or debug_pause_at_start:
        dbg = {"enable_on_start": True, "pause_at_start": bool(debug_pause_at_start), "action": "enable_now"}

    params: Dict[str, Any] = {"operation": "start", "hot_reload": hot_reload}

    # Prefer new_worker if provided (official path)
    if isinstance(new_worker, dict) and (new_worker.get("first_name") and new_worker.get("template")):
        # NEW: require leader_name when creating a new worker
        if not (leader_name and str(leader_name).strip()):
            return {"accepted": False, "status": "error", "code": "LEADER_REQUIRED", "message": "leader_name is required when creating a new worker"}
        params["new_worker"] = {"first_name": str(new_worker["first_name"]).strip(), "template": str(new_worker["template"]).strip()}
    else:
        # Legacy: keep worker_name/worker_file (UI older flows)
        if worker_name:
            params["worker_name"] = worker_name
        if worker_file:
            params["worker_file"] = worker_file

    if dbg:
        params["debug"] = dbg
    if leader_name:
        params["leader"] = {"name": leader_name}

    # Fallback robustesse: si on démarre un worker existant sans worker_file,
    # réutiliser le worker_file mémorisé en DB KV (cas legacy sans identity.template)
    if ("worker_name" in params) and (not params.get("worker_file")):
        try:
            from src.tools._py_orchestrator.api_spawn import db_path_for_worker
            from src.tools._py_orchestrator.db import get_state_kv
            dbp = db_path_for_worker(params["worker_name"])
            wf_prev = get_state_kv(dbp, params["worker_name"], 'worker_file') or ''
            if wf_prev:
                params["worker_file"] = wf_prev
        except Exception:
            pass

    return py_route(params)

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
