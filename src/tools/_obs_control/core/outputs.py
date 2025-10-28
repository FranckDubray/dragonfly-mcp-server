from __future__ import annotations
from typing import Any, Dict
from ..services import obs_client
import time


def _get_state() -> Dict[str, Any]:
    r = obs_client.call("GetStreamStatus")
    if not r.get("ok"):
        return {"ok": False, "error": r.get("error", "obs_error")}
    d = r.get("data", {})
    state = "active" if d.get("outputActive") else ("reconnecting" if d.get("outputReconnecting") else "inactive")
    return {"ok": True, "state": state, "uptime_sec": d.get("outputTimecode"), "bytes": d.get("outputBytes"), "skipped_frames": d.get("outputSkippedFrames")}


def stream_status(session_id: str | None, timeout_sec: int | None) -> Dict[str, Any]:
    return _get_state()


def stream_start(args: Dict[str, Any], session_id: str | None, wait: bool, timeout_sec: int | None, dry_run: bool) -> Dict[str, Any]:
    if not args.get("confirm", False) and not dry_run:
        return {"ok": False, "error": "confirmation_required"}
    if dry_run:
        return {"ok": True, "plan": "StartStream"}
    r = obs_client.call("StartStream")
    if not r.get("ok"):
        return r
    if not wait:
        return {"ok": True, "state": "starting"}
    # Attente jusqu'à actif ou timeout
    deadline = time.time() + (timeout_sec or 20)
    while time.time() < deadline:
        st = _get_state()
        if st.get("ok") and st.get("state") == "active":
            return st
        time.sleep(0.3)
    return {"ok": False, "error": "timeout", "message": "Stream non actif dans le délai"}


def stream_stop(args: Dict[str, Any], session_id: str | None, wait: bool, timeout_sec: int | None, dry_run: bool) -> Dict[str, Any]:
    if not args.get("confirm", False) and not dry_run:
        return {"ok": False, "error": "confirmation_required"}
    if dry_run:
        return {"ok": True, "plan": "StopStream"}
    r = obs_client.call("StopStream")
    if not r.get("ok"):
        return r
    if not wait:
        return {"ok": True, "state": "stopping"}
    # Attente jusqu'à inactif ou timeout
    deadline = time.time() + (timeout_sec or 10)
    while time.time() < deadline:
        st = _get_state()
        if st.get("ok") and st.get("state") == "inactive":
            return st
        time.sleep(0.3)
    return {"ok": False, "error": "timeout", "message": "Stream non arrêté dans le délai"}
