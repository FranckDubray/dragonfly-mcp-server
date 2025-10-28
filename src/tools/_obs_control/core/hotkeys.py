from __future__ import annotations
from typing import Any, Dict, List
from ..services import obs_client


def list_hotkeys(args: Dict[str, Any]) -> Dict[str, Any]:
    r = obs_client.call("GetHotkeyList")
    if not r.get("ok"):
        return r
    keys: List[str] = r.get("data", {}).get("hotkeys", []) or []
    return {"ok": True, "hotkeys": keys, "total_count": len(keys), "returned_count": len(keys), "truncated": False}


def trigger_by_name(args: Dict[str, Any]) -> Dict[str, Any]:
    name = args.get("hotkey_name")
    if not isinstance(name, str) or not name:
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("TriggerHotkeyByName", {"hotkeyName": name})
    return r if not r.get("ok") else {"ok": True, "triggered": True}


def trigger_by_keys(args: Dict[str, Any]) -> Dict[str, Any]:
    key = args.get("key"); modifiers = args.get("modifiers") or []
    if not isinstance(key, str):
        return {"ok": False, "error": "invalid_argument"}
    if not isinstance(modifiers, list):
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("TriggerHotkeyByKeySequence", {"keyId": key, "keyModifiers": {"shift": "SHIFT" in modifiers, "control": "CTRL" in modifiers, "alt": "ALT" in modifiers, "command": "CMD" in modifiers}})
    return r if not r.get("ok") else {"ok": True, "triggered": True}
