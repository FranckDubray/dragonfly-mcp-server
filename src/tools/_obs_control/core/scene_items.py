from __future__ import annotations
from typing import Any, Dict, List, Optional
from ..services import obs_client


def _resolve_item_id(scene_name: str, scene_item_id: Optional[int], source_name: Optional[str]) -> Dict[str, Any]:
    if isinstance(scene_item_id, int):
        return {"ok": True, "id": scene_item_id}
    if not isinstance(source_name, str) or not source_name:
        return {"ok": False, "error": "invalid_argument", "message": "scene_item_id ou source_name requis"}
    lst = obs_client.call("GetSceneItemList", {"sceneName": scene_name})
    if not lst.get("ok"):
        return lst
    items = lst.get("data", {}).get("sceneItems", []) or []
    matches = [it for it in items if it.get("sourceName") == source_name]
    if not matches:
        return {"ok": False, "error": "not_found"}
    if len(matches) > 1:
        return {"ok": False, "error": "ambiguous", "message": "Plusieurs items correspondent; précisez scene_item_id"}
    return {"ok": True, "id": matches[0].get("sceneItemId")}


def list_items(args: Dict[str, Any]) -> Dict[str, Any]:
    scene_name = args.get("scene_name")
    if not isinstance(scene_name, str) or not scene_name:
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("GetSceneItemList", {"sceneName": scene_name})
    if not r.get("ok"):
        return r
    items: List[Dict[str, Any]] = r.get("data", {}).get("sceneItems", []) or []
    limit = args.get("limit", 50)
    try:
        limit = int(limit)
    except Exception:
        limit = 50
    limit = max(1, min(500, limit))
    total = len(items)
    out = items[:limit]
    return {"ok": True, "items": out, "total_count": total, "returned_count": len(out), "truncated": total > len(out)}


def set_enabled(args: Dict[str, Any]) -> Dict[str, Any]:
    scene_name = args.get("scene_name")
    scene_item_id = args.get("scene_item_id")
    source_name = args.get("source_name")
    enabled = args.get("enabled")
    if not isinstance(scene_name, str) or not isinstance(enabled, bool):
        return {"ok": False, "error": "invalid_argument"}
    rid = _resolve_item_id(scene_name, scene_item_id, source_name)
    if not rid.get("ok"):
        return rid
    r = obs_client.call("SetSceneItemEnabled", {"sceneName": scene_name, "sceneItemId": rid.get("id"), "sceneItemEnabled": enabled})
    return r if not r.get("ok") else {"ok": True, "changed": True}


def set_transform(args: Dict[str, Any]) -> Dict[str, Any]:
    scene_name = args.get("scene_name")
    scene_item_id = args.get("scene_item_id")
    transform = args.get("transform") or {}
    if not isinstance(scene_name, str) or not isinstance(scene_item_id, int) or not isinstance(transform, dict):
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("SetSceneItemTransform", {"sceneName": scene_name, "sceneItemId": scene_item_id, "sceneItemTransform": transform})
    return r if not r.get("ok") else {"ok": True, "applied": True}


def set_order(args: Dict[str, Any]) -> Dict[str, Any]:
    scene_name = args.get("scene_name"); scene_item_id = args.get("scene_item_id"); index = args.get("index")
    if not isinstance(scene_name, str) or not isinstance(scene_item_id, int) or not isinstance(index, int):
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("SetSceneItemIndex", {"sceneName": scene_name, "sceneItemId": scene_item_id, "sceneItemIndex": index})
    return r if not r.get("ok") else {"ok": True, "applied": True}


def add(args: Dict[str, Any]) -> Dict[str, Any]:
    scene_name = args.get("scene_name"); input_name = args.get("input_name")
    if not isinstance(scene_name, str) or not isinstance(input_name, str):
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("CreateSceneItem", {"sceneName": scene_name, "sourceName": input_name, "sceneItemEnabled": True})
    return r if not r.get("ok") else {"ok": True, "sceneItemId": r.get("data", {}).get("sceneItemId")}


def remove(args: Dict[str, Any]) -> Dict[str, Any]:
    if not args.get("confirm", False):
        return {"ok": False, "error": "confirmation_required"}
    scene_name = args.get("scene_name"); scene_item_id = args.get("scene_item_id")
    if not isinstance(scene_name, str) or not isinstance(scene_item_id, int):
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("RemoveSceneItem", {"sceneName": scene_name, "sceneItemId": scene_item_id})
    return r if not r.get("ok") else {"ok": True, "removed": True}


def set_locked(args: Dict[str, Any]) -> Dict[str, Any]:
    scene_name = args.get("scene_name"); scene_item_id = args.get("scene_item_id"); locked = args.get("locked")
    if not isinstance(scene_name, str) or not isinstance(scene_item_id, int) or not isinstance(locked, bool):
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("SetSceneItemLocked", {"sceneName": scene_name, "sceneItemId": scene_item_id, "sceneItemLocked": locked})
    return r if not r.get("ok") else {"ok": True, "locked": locked}
