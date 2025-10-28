from __future__ import annotations
from typing import Any, Dict, List
from ..services import obs_client
from . import transitions_override as core_override
import time


def list_scenes(args: Dict[str, Any]) -> Dict[str, Any]:
    r = obs_client.call("GetSceneList")
    if not r.get("ok"):
        return r
    d = r.get("data", {})
    scenes = [s.get("sceneName") for s in (d.get("scenes", []) or [])]
    prog = d.get("currentProgramSceneName")
    prev = d.get("currentPreviewSceneName")
    limit = args.get("limit", 50)
    try:
        limit = int(limit)
    except Exception:
        limit = 50
    limit = max(1, min(500, limit))
    total = len(scenes)
    out = scenes[:limit]
    return {"ok": True, "scenes": out, "program": prog, "preview": prev, "total_count": total, "returned_count": len(out), "truncated": total > len(out)}


def create(args: Dict[str, Any]) -> Dict[str, Any]:
    name = args.get("scene_name")
    if not isinstance(name, str) or not name:
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("CreateScene", {"sceneName": name})
    return r if not r.get("ok") else {"ok": True, "created": True}


def delete(args: Dict[str, Any]) -> Dict[str, Any]:
    if not args.get("confirm", False):
        return {"ok": False, "error": "confirmation_required"}
    name = args.get("scene_name")
    if not isinstance(name, str) or not name:
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("RemoveScene", {"sceneName": name})
    return r if not r.get("ok") else {"ok": True, "deleted": True}


def rename(args: Dict[str, Any]) -> Dict[str, Any]:
    name = args.get("scene_name"); new = args.get("new_name")
    if not isinstance(name, str) or not isinstance(new, str):
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("SetSceneName", {"sceneName": name, "newSceneName": new})
    return r if not r.get("ok") else {"ok": True, "renamed": True}


def set_default_transition(args: Dict[str, Any]) -> Dict[str, Any]:
    # Confort: wrap override_set
    scene = args.get("scene_name")
    if not isinstance(scene, str) or not scene:
        return {"ok": False, "error": "invalid_argument"}
    return core_override.override_set(args)


def set_current(args: Dict[str, Any], session_id: str | None, wait: bool, timeout_sec: int | None, dry_run: bool) -> Dict[str, Any]:
    name = args.get("scene_name")
    if not isinstance(name, str) or not name:
        return {"ok": False, "error": "invalid_argument", "message": "scene_name requis"}
    before = obs_client.call("GetCurrentProgramScene")
    if not before.get("ok"):
        return before
    cur = before.get("data", {}).get("currentProgramSceneName")
    if dry_run:
        return {"ok": True, "before": cur, "after": name, "changed": cur != name}
    if cur != name:
        r = obs_client.call("SetCurrentProgramScene", {"sceneName": name})
        if not r.get("ok"):
            return r
    after = obs_client.call("GetCurrentProgramScene")
    return {"ok": True, "before": cur, "after": after.get("data", {}).get("currentProgramSceneName"), "changed": cur != name}


def set_preview(args: Dict[str, Any], session_id: str | None, timeout_sec: int | None, dry_run: bool) -> Dict[str, Any]:
    name = args.get("scene_name")
    if not isinstance(name, str) or not name:
        return {"ok": False, "error": "invalid_argument", "message": "scene_name requis"}
    if dry_run:
        return {"ok": True, "preview": name}
    r = obs_client.call("SetCurrentPreviewScene", {"sceneName": name})
    if not r.get("ok"):
        return r
    after = obs_client.call("GetCurrentPreviewScene")
    return {"ok": True, "preview": after.get("data", {}).get("currentPreviewSceneName")}


def transition_to_program(args: Dict[str, Any], session_id: str | None, wait: bool, timeout_sec: int | None) -> Dict[str, Any]:
    # Mémoriser la preview avant la transition pour valider le résultat si wait=True
    prev = obs_client.call("GetCurrentPreviewScene")
    prev_name = prev.get("data", {}).get("currentPreviewSceneName") if prev.get("ok") else None

    req: Dict[str, Any] = {}
    if isinstance(args.get("transition_name"), str):
        req["withTransition"] = {"transitionName": args["transition_name"]}
    if isinstance(args.get("duration_ms"), int):
        req.setdefault("withTransition", {})["transitionDuration"] = args["duration_ms"]
    r = obs_client.call("TriggerStudioModeTransition", req or None)
    if not r.get("ok"):
        return r

    if not wait:
        return {"ok": True, "done": True}

    # Attente jusqu'à ce que la scène programme corresponde à l'ancienne preview
    deadline = time.time() + (timeout_sec or 5)
    while time.time() < deadline:
        prog = obs_client.call("GetCurrentProgramScene")
        if prog.get("ok") and (prev_name is None or prog.get("data", {}).get("currentProgramSceneName") == prev_name):
            return {"ok": True, "done": True}
        time.sleep(0.3)
    return {"ok": False, "error": "timeout", "message": "Transition studio non terminée dans le délai"}
