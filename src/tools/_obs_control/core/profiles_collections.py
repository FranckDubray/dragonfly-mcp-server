from __future__ import annotations
from typing import Any, Dict, List
from ..services import obs_client


def profiles_list(args: Dict[str, Any]) -> Dict[str, Any]:
    r = obs_client.call("GetProfileList")
    if not r.get("ok"):
        return r
    cur = r.get("data", {}).get("currentProfileName")
    lst: List[str] = r.get("data", {}).get("profiles", []) or []
    return {"ok": True, "current": cur, "profiles": lst, "total_count": len(lst), "returned_count": len(lst), "truncated": False}


def profiles_set_current(args: Dict[str, Any]) -> Dict[str, Any]:
    if not args.get("confirm", False):
        return {"ok": False, "error": "confirmation_required"}
    name = args.get("profile_name")
    if not isinstance(name, str):
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("SetCurrentProfile", {"profileName": name})
    return r if not r.get("ok") else {"ok": True, "current": name}


def scene_collections_list(args: Dict[str, Any]) -> Dict[str, Any]:
    r = obs_client.call("GetSceneCollectionList")
    if not r.get("ok"):
        return r
    cur = r.get("data", {}).get("currentSceneCollectionName")
    lst: List[str] = r.get("data", {}).get("sceneCollections", []) or []
    return {"ok": True, "current": cur, "collections": lst, "total_count": len(lst), "returned_count": len(lst), "truncated": False}


def scene_collections_set_current(args: Dict[str, Any]) -> Dict[str, Any]:
    if not args.get("confirm", False):
        return {"ok": False, "error": "confirmation_required"}
    name = args.get("collection_name")
    if not isinstance(name, str):
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("SetCurrentSceneCollection", {"sceneCollectionName": name})
    return r if not r.get("ok") else {"ok": True, "current": name}
