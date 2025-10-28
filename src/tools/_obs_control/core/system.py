from __future__ import annotations
from typing import Any, Dict
from ..services import obs_client


def get_version(args: Dict[str, Any] | None = None) -> Dict[str, Any]:
    r = obs_client.call("GetVersion")
    return r if not r.get("ok") else {"ok": True, **r.get("data", {})}
