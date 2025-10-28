from __future__ import annotations
from typing import Any, Dict
from ..services import obs_client


def balance_set(args: Dict[str, Any]) -> Dict[str, Any]:
    name = args.get("input_name"); bal = args.get("balance")
    if not isinstance(name, str) or not isinstance(bal, (int, float)):
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("SetInputAudioBalance", {"inputName": name, "inputAudioBalance": float(bal)})
    return r if not r.get("ok") else {"ok": True}


def sync_offset_set(args: Dict[str, Any]) -> Dict[str, Any]:
    name = args.get("input_name"); offs = args.get("offset_ms")
    if not isinstance(name, str) or not isinstance(offs, int):
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("SetInputAudioSyncOffset", {"inputName": name, "inputAudioSyncOffset": offs})
    return r if not r.get("ok") else {"ok": True}
