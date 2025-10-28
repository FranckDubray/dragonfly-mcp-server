from __future__ import annotations
from typing import Any, Dict
from ..services import obs_client


def record_start(args: Dict[str, Any]) -> Dict[str, Any]:
    r = obs_client.call("StartRecord")
    return r if not r.get("ok") else {"ok": True, "state": "starting"}


def record_stop(args: Dict[str, Any]) -> Dict[str, Any]:
    if not args.get("confirm", False):
        return {"ok": False, "error": "confirmation_required"}
    r = obs_client.call("StopRecord")
    return r if not r.get("ok") else {"ok": True, "state": "stopping"}


def record_pause(args: Dict[str, Any]) -> Dict[str, Any]:
    r = obs_client.call("ToggleRecordPause")
    return r if not r.get("ok") else {"ok": True}


def record_resume(args: Dict[str, Any]) -> Dict[str, Any]:
    r = obs_client.call("ToggleRecordPause")
    return r if not r.get("ok") else {"ok": True}


def record_status(args: Dict[str, Any]) -> Dict[str, Any]:
    r = obs_client.call("GetRecordStatus")
    return r if not r.get("ok") else {"ok": True, **r.get("data", {})}


def replay_start(args: Dict[str, Any]) -> Dict[str, Any]:
    r = obs_client.call("StartReplayBuffer")
    return r if not r.get("ok") else {"ok": True}


def replay_stop(args: Dict[str, Any]) -> Dict[str, Any]:
    r = obs_client.call("StopReplayBuffer")
    return r if not r.get("ok") else {"ok": True}


def replay_save(args: Dict[str, Any]) -> Dict[str, Any]:
    if not args.get("confirm", False):
        return {"ok": False, "error": "confirmation_required"}
    r = obs_client.call("SaveReplayBuffer")
    return r if not r.get("ok") else {"ok": True}


def replay_status(args: Dict[str, Any]) -> Dict[str, Any]:
    r = obs_client.call("GetReplayBufferStatus")
    return r if not r.get("ok") else {"ok": True, **r.get("data", {})}


def virtualcam_start(args: Dict[str, Any]) -> Dict[str, Any]:
    r = obs_client.call("StartVirtualCam")
    return r if not r.get("ok") else {"ok": True}


def virtualcam_stop(args: Dict[str, Any]) -> Dict[str, Any]:
    r = obs_client.call("StopVirtualCam")
    return r if not r.get("ok") else {"ok": True}


def virtualcam_status(args: Dict[str, Any]) -> Dict[str, Any]:
    r = obs_client.call("GetVirtualCamStatus")
    return r if not r.get("ok") else {"ok": True, **r.get("data", {})}


def stream_service_get(args: Dict[str, Any]) -> Dict[str, Any]:
    r = obs_client.call("GetStreamServiceSettings")
    return r if not r.get("ok") else {"ok": True, **r.get("data", {})}


def stream_service_set(args: Dict[str, Any]) -> Dict[str, Any]:
    settings = args.get("settings") or {}
    if not isinstance(settings, dict):
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("SetStreamServiceSettings", {"streamServiceSettings": settings})
    return r if not r.get("ok") else {"ok": True, "applied": True}
