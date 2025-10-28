from __future__ import annotations
from typing import Any, Dict
from ..services import obs_client


def set_enabled(args: Dict[str, Any]) -> Dict[str, Any]:
    enabled = args.get("enabled")
    if not isinstance(enabled, bool):
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("SetStudioModeEnabled", {"studioModeEnabled": enabled})
    return r if not r.get("ok") else {"ok": True, "studio_mode": enabled}
