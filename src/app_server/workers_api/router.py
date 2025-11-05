











from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, Dict, Any

router = APIRouter(prefix="/workers/api", tags=["workers-api"])

from . import list_api, status_api, config_api, start_stop_api, debug_api, debug_stream_api, leader_chat_api, replay_api, identity_api, leader_identity_api, leader_chat_leader_api, kpis_api, observe_many_api, templates_api, images_api, leader_list_api

@router.get("/list")
async def api_list(leader: Optional[str] = Query(None)):
    res = await list_api.get_list(leader)
    return res or {"accepted": False, "status": "error"}

@router.get("/status")
async def api_status(worker: str = Query(..., min_length=1)):
    res = await status_api.get_status(worker)
    return res or {"accepted": False, "status": "error"}

@router.get("/config")
async def api_config(worker: str = Query(..., min_length=1)):
    res = await config_api.get_config(worker)
    return res or {"accepted": False, "status": "error"}

@router.post("/start")
async def api_start(
    # Legacy (query)
    worker: Optional[str] = Query(None, min_length=1),
    worker_file: Optional[str] = None,
    hot_reload: bool = True,
    debug_enable: bool = False,
    debug_pause_at_start: bool = False,
    leader_name: Optional[str] = None,
    # Official: new_worker in JSON body
    body: Optional[Dict[str, Any]] = Body(None),
):
    new_worker: Optional[Dict[str, Any]] = None
    try:
        if isinstance(body, dict):
            nw = body.get('new_worker')
            if isinstance(nw, dict) and (nw.get('first_name') and nw.get('template')):
                new_worker = { 'first_name': str(nw['first_name']).strip(), 'template': str(nw['template']).strip() }
    except Exception:
        new_worker = None
    res = await start_stop_api.start_worker(
        worker_name=worker,
        worker_file=worker_file,
        hot_reload=hot_reload,
        debug_enable=debug_enable,
        debug_pause_at_start=debug_pause_at_start,
        leader_name=leader_name,
        new_worker=new_worker,
    )
    return res or {"accepted": False, "status": "error"}

@router.post("/stop")
async def api_stop(worker: str = Query(..., min_length=1), mode: str = Query("soft", regex="^(soft|term|kill)$")):
    res = await start_stop_api.stop_worker(worker_name=worker, mode=mode)
    return res or {"accepted": False, "status": "error"}

@router.post("/debug")
async def api_debug(
    worker: str = Query(..., min_length=1),
    action: str = Query(..., regex="^(enable|enable_now|step|continue|run_until|break_add|break_remove|break_clear|break_list|inspect|disable)$"),
    timeout_sec: Optional[float] = None,
    target_node: Optional[str] = None,
    target_when: Optional[str] = None,
    break_node: Optional[str] = None,
    break_when: Optional[str] = None,
):
    res = await debug_api.debug_action(
        worker_name=worker,
        action=action,
        timeout_sec=timeout_sec,
        target_node=target_node,
        target_when=target_when,
        break_node=break_node,
        break_when=break_when,
    )
    return res or {"accepted": False, "status": "error"}

@router.get("/debug/stream")
async def api_debug_stream(worker: str, timeout_sec: float = 10.0, max_events: int = 50):
    return await debug_stream_api.stream_ndjson(worker, timeout_sec, max_events)

# NEW: observe (passive) SSE endpoint for the SPA (no LLM use)
@router.get("/observe/stream")
async def api_observe_stream(worker: str, timeout_sec: float = 30.0, max_events: int = 200):
    from . import observe_stream_api
    return await observe_stream_api.stream_ndjson(worker, timeout_sec, max_events)

@router.post("/leader_chat")
async def api_leader_chat(worker: str, message: str, model: Optional[str] = "gpt-5-mini", history_limit: int = 20):
    res = await leader_chat_api.post_message(worker, message, model or "gpt-5-mini", history_limit)
    return res or {"accepted": False, "status": "error"}

@router.get("/leader_chat")
async def api_leader_history(worker: str, limit: int = 30):
    res = await leader_chat_api.get_history(worker)
    return res or {"accepted": False, "status": "error"}

@router.get("/replay/runs")
async def api_replay_runs(worker: str, limit: int = 20):
    res = await replay_api.list_runs(worker, limit)
    return res or {"accepted": False, "status": "error"}

@router.get("/replay/steps")
async def api_replay_steps(worker: str, run_id: Optional[str] = None, limit: int = 500):
    res = await replay_api.get_steps(worker, run_id, limit)
    return res or {"accepted": False, "status": "error"}

@router.get("/identity")
async def api_identity_get(worker: str = Query(..., min_length=1)):
    res = await identity_api.get_identity(worker)
    return res or {"accepted": False, "status": "not_found"}

@router.post("/identity")
async def api_identity_update(worker: str = Query(..., min_length=1), patch: Dict[str, Any] = Body(...)):
    res = await identity_api.update_identity(worker, patch)
    return res or {"accepted": False, "status": "not_found"}

@router.get("/leader_identity")
async def api_leader_get(name: str):
    res = await leader_identity_api.get_identity(name)
    return res or {"accepted": False, "status": "not_found"}

@router.post("/leader_identity")
async def api_leader_update(name: str, patch: Dict[str, Any] = Body(...)):
    res = await leader_identity_api.update_identity(name, patch)
    return res or {"accepted": False, "status": "not_found"}

@router.post("/leader_chat_global")
async def api_leader_chat_global(name: str, message: str, model: Optional[str] = "gpt-5-mini", history_limit: int = 20):
    res = await leader_chat_leader_api.post_message(name, message, model or "gpt-5-mini", history_limit)
    return res or {"accepted": False, "status": "error"}

@router.get("/leader_chat_global")
async def api_leader_chat_global_history(name: str, limit: int = 30):
    res = await leader_chat_leader_api.get_history(name, limit)
    return res or {"accepted": False, "status": "error"}

@router.get("/kpis")
async def api_kpis():
    res = await kpis_api.get_kpis()
    return res or {"accepted": False, "status": "error"}

@router.get("/observe_many")
async def api_observe_many(timeout_sec: float = 15.0, max_events: int = 200):
    return await observe_many_api.stream_ndjson(timeout_sec, max_events)

@router.get("/templates")
async def api_templates(name: Optional[str] = Query(None)):
    if name:
        res = await templates_api.get_template(name)
    else:
        res = await templates_api.list_templates()
    return res or {"accepted": False, "status": "error"}

@router.get("/avatars")
async def api_avatars():
    res = await images_api.list_avatars()
    return res or {"accepted": False, "status": "error"}

@router.get("/leaders")
async def api_leaders():
    res = await leader_list_api.list_leaders()
    return res or {"accepted": False, "status": "error"}
