from __future__ import annotations
from typing import Any, Dict
from ..services import obs_client
import time


def status(args: Dict[str, Any]) -> Dict[str, Any]:
    name = args.get("input_name")
    if not isinstance(name, str) or not name:
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("GetMediaInputStatus", {"inputName": name})
    if not r.get("ok"):
        return r
    d = r.get("data", {})
    return {
        "ok": True,
        "state": d.get("mediaState"),
        "position_ms": d.get("mediaCursor"),
        "duration_ms": d.get("mediaDuration"),
        "loop": d.get("mediaLooping"),
    }


def action(args: Dict[str, Any], wait: bool = False, timeout_sec: int | None = None) -> Dict[str, Any]:
    name = args.get("input_name"); act = args.get("action")
    if not isinstance(name, str) or not isinstance(act, str):
        return {"ok": False, "error": "invalid_argument"}
    mapping = {
        "play": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PLAY",
        "pause": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PAUSE",
        "stop": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_STOP",
        "restart": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART",
        "next": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_NEXT",
        "previous": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PREVIOUS",
        "toggle_loop": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_TOGGLE_LOOP",
    }
    obs_act = mapping.get(act)
    if not obs_act:
        return {"ok": False, "error": "invalid_argument", "message": "action inconnue"}
    r = obs_client.call("TriggerMediaInputAction", {"inputName": name, "mediaAction": obs_act})
    if not r.get("ok"):
        return r
    if not wait:
        return {"ok": True, "done": True}
    # Attente basique: si stop/restart → attendre position=0 ou state in {stopped, playing}; si play → attendre état playing; si pause → paused
    deadline = time.time() + (timeout_sec or 10)
    target_states = {
        "play": {"playing"},
        "pause": {"paused"},
        "stop": {"stopped"},
        "restart": {"playing", "stopped"},
        "next": {"playing", "stopped", "paused"},
        "previous": {"playing", "stopped", "paused"},
        "toggle_loop": {"playing", "paused", "stopped"},
    }.get(act, set())
    while time.time() < deadline:
        st = status({"input_name": name})
        if st.get("ok"):
            state = (st.get("state") or "").lower()
            if not target_states or state in target_states:
                return {"ok": True, "state": state, "position_ms": st.get("position_ms"), "duration_ms": st.get("duration_ms")}
        time.sleep(0.3)
    return {"ok": False, "error": "timeout", "message": "Média: état cible non atteint dans le délai"}


def seek(args: Dict[str, Any]) -> Dict[str, Any]:
    name = args.get("input_name"); cursor = args.get("cursor_ms")
    if not isinstance(name, str) or not isinstance(cursor, int):
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("SetMediaInputCursor", {"inputName": name, "mediaCursor": cursor})
    return r if not r.get("ok") else {"ok": True, "position_ms": cursor}
