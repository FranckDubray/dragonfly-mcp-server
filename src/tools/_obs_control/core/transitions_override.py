from __future__ import annotations
from typing import Any, Dict
from ..services import obs_client


def override_get(args: Dict[str, Any]) -> Dict[str, Any]:
    scene = args.get("scene_name")
    if not isinstance(scene, str) or not scene:
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("GetSceneSceneTransitionOverride", {"sceneName": scene})
    return r if not r.get("ok") else {"ok": True, **r.get("data", {})}


def override_set(args: Dict[str, Any]) -> Dict[str, Any]:
    scene = args.get("scene_name"); tname = args.get("transition_name"); dur = args.get("duration_ms")
    if not isinstance(scene, str):
        return {"ok": False, "error": "invalid_argument"}
    payload: Dict[str, Any] = {"sceneName": scene}
    if isinstance(tname, str):
        payload["transitionName"] = tname
    if isinstance(dur, int):
        payload["transitionDuration"] = dur
    r = obs_client.call("SetSceneSceneTransitionOverride", payload)
    return r if not r.get("ok") else {"ok": True}
