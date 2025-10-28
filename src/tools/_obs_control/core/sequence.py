from __future__ import annotations
from typing import Any, Dict, List, Callable
import time
from ..services import obs_client

"""
Séquenceur d'étapes (exécution synchrone, courtes connexions, pas d'event long).
Steps supportés (name -> args):
- set_transition {name, duration_ms?}
- set_preview {scene_name}
- set_program {scene_name}
- media_action {input_name, action}
- wait_sec {seconds}
- wait_media_end {input_name, timeout_sec?}
- transition_to_program {transition_name?, duration_ms?}
- set_mute {input_name, muted}
- set_volume {input_name, volume_db? | volume_mul?}
"""


def run_steps(steps: List[Dict[str, Any]], cancel_flag: Callable[[], bool]) -> None:
    for step in steps:
        if cancel_flag():
            return
        if not isinstance(step, dict):
            continue
        name = step.get("name")
        args = step.get("args") or {}
        if name == "set_transition":
            _set_transition(args)
        elif name == "set_preview":
            _set_preview(args)
        elif name == "set_program":
            _set_program(args)
        elif name == "media_action":
            _media_action(args)
        elif name == "wait_sec":
            _wait_sec(args)
        elif name == "wait_media_end":
            _wait_media_end(args, cancel_flag)
        elif name == "transition_to_program":
            _transition_to_program(args)
        elif name == "set_mute":
            _set_mute(args)
        elif name == "set_volume":
            _set_volume(args)
        else:
            continue


def _set_transition(args: Dict[str, Any]) -> None:
    name = args.get("name"); dur = args.get("duration_ms")
    if isinstance(name, str):
        obs_client.call("SetCurrentSceneTransition", {"transitionName": name})
    if isinstance(dur, int):
        obs_client.call("SetCurrentSceneTransitionDuration", {"transitionDuration": dur})


def _set_preview(args: Dict[str, Any]) -> None:
    scene = args.get("scene_name")
    if isinstance(scene, str) and scene:
        obs_client.call("SetCurrentPreviewScene", {"sceneName": scene})


def _set_program(args: Dict[str, Any]) -> None:
    scene = args.get("scene_name")
    if isinstance(scene, str) and scene:
        obs_client.call("SetCurrentProgramScene", {"sceneName": scene})


def _media_action(args: Dict[str, Any]) -> None:
    name = args.get("input_name"); act = args.get("action")
    if not isinstance(name, str) or not isinstance(act, str):
        return
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
        return
    obs_client.call("TriggerMediaInputAction", {"inputName": name, "mediaAction": obs_act})


def _wait_sec(args: Dict[str, Any]) -> None:
    sec = args.get("seconds")
    try:
        s = max(0, float(sec))
    except Exception:
        s = 0
    time.sleep(s)


def _wait_media_end(args: Dict[str, Any], cancel_flag) -> None:
    name = args.get("input_name"); timeout_sec = args.get("timeout_sec", 600)
    end_deadline = time.time() + max(1, int(timeout_sec))
    while time.time() < end_deadline and not cancel_flag():
        st = obs_client.call("GetMediaInputStatus", {"inputName": name})
        if st.get("ok"):
            d = st.get("data", {})
            state = str(d.get("mediaState") or "").lower()
            if state in {"ended", "stopped"}:
                return
        time.sleep(0.5)
    # Timeout silencieux
    return


def _transition_to_program(args: Dict[str, Any]) -> None:
    req: Dict[str, Any] = {}
    if isinstance(args.get("transition_name"), str):
        req["withTransition"] = {"transitionName": args["transition_name"]}
    if isinstance(args.get("duration_ms"), int):
        req.setdefault("withTransition", {})["transitionDuration"] = args["duration_ms"]
    obs_client.call("TriggerStudioModeTransition", req or None)


def _set_mute(args: Dict[str, Any]) -> None:
    name = args.get("input_name"); muted = args.get("muted")
    if not isinstance(name, str) or not isinstance(muted, bool):
        return
    obs_client.call("SetInputMute", {"inputName": name, "inputMuted": muted})


def _set_volume(args: Dict[str, Any]) -> None:
    name = args.get("input_name")
    if not isinstance(name, str):
        return
    req: Dict[str, Any] = {"inputName": name}
    vol_db = args.get("volume_db"); vol_mul = args.get("volume_mul")
    if isinstance(vol_db, (int, float)):
        req["inputVolumeDb"] = float(vol_db)
    if isinstance(vol_mul, (int, float)):
        req["inputVolumeMul"] = float(vol_mul)
    if len(req) == 1:
        return
    obs_client.call("SetInputVolume", req)
