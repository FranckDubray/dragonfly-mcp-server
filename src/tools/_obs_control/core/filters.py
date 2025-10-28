from __future__ import annotations
from typing import Any, Dict, List
from ..services import obs_client


def list_filters(args: Dict[str, Any]) -> Dict[str, Any]:
    src = args.get("source_name")
    if not isinstance(src, str) or not src:
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("GetSourceFilterList", {"sourceName": src})
    if not r.get("ok"):
        return r
    flt: List[Dict[str, Any]] = r.get("data", {}).get("filters", []) or []
    return {"ok": True, "filters": flt, "total_count": len(flt), "returned_count": len(flt), "truncated": False}


def add(args: Dict[str, Any]) -> Dict[str, Any]:
    src = args.get("source_name"); name = args.get("filter_name"); kind = args.get("filter_kind"); settings = args.get("settings") or {}
    if not all(isinstance(x, str) and x for x in [src, name, kind]) or not isinstance(settings, dict):
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("CreateSourceFilter", {"sourceName": src, "filterName": name, "filterKind": kind, "filterSettings": settings})
    return r if not r.get("ok") else {"ok": True, "created": True}


def remove(args: Dict[str, Any]) -> Dict[str, Any]:
    if not args.get("confirm", False):
        return {"ok": False, "error": "confirmation_required"}
    src = args.get("source_name"); name = args.get("filter_name")
    if not isinstance(src, str) or not isinstance(name, str):
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("RemoveSourceFilter", {"sourceName": src, "filterName": name})
    return r if not r.get("ok") else {"ok": True, "removed": True}


def rename(args: Dict[str, Any]) -> Dict[str, Any]:
    src = args.get("source_name"); name = args.get("filter_name"); new = args.get("new_name")
    if not all(isinstance(x, str) for x in [src, name, new]):
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("SetSourceFilterName", {"sourceName": src, "filterName": name, "newFilterName": new})
    return r if not r.get("ok") else {"ok": True, "renamed": True}


def set_enabled(args: Dict[str, Any]) -> Dict[str, Any]:
    src = args.get("source_name"); name = args.get("filter_name"); enabled = args.get("enabled")
    if not isinstance(src, str) or not isinstance(name, str) or not isinstance(enabled, bool):
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("SetSourceFilterEnabled", {"sourceName": src, "filterName": name, "filterEnabled": enabled})
    return r if not r.get("ok") else {"ok": True, "enabled": enabled}


def set_settings(args: Dict[str, Any]) -> Dict[str, Any]:
    src = args.get("source_name"); name = args.get("filter_name"); settings = args.get("settings") or {}
    if not isinstance(src, str) or not isinstance(name, str) or not isinstance(settings, dict):
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("SetSourceFilterSettings", {"sourceName": src, "filterName": name, "filterSettings": settings})
    return r if not r.get("ok") else {"ok": True, "applied": True}
