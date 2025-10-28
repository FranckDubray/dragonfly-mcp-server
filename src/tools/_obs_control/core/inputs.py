from __future__ import annotations
from typing import Any, Dict, List
from ..services import obs_client
from ..services.path_guard import normalize_local_path

# Helpers simples pour protéger certains réglages de chemins
PATH_KEYS = {"local_file", "file", "file_path", "image_path", "movie", "media"}


def _guard_settings_paths(settings: Dict[str, Any]) -> Dict[str, Any] | Dict[str, Any]:
    if not isinstance(settings, dict):
        return settings
    sanitized = dict(settings)
    for k, v in list(sanitized.items()):
        if k in PATH_KEYS and isinstance(v, str):
            ok, abs_path, err = normalize_local_path(v)
            if not ok:
                return {"ok": False, "error": "invalid_path", "message": f"{k} interdit ou hors ./docs", "code": err}
            # On passe le chemin absolu validé à OBS
            sanitized[k] = abs_path
    return sanitized


def inputs_list(args: Dict[str, Any]) -> Dict[str, Any]:
    r = obs_client.call("GetInputList")
    if not r.get("ok"):
        return r
    items: List[Dict[str, Any]] = r.get("data", {}).get("inputs", []) or []
    limit = args.get("limit", 50)
    try:
        limit = int(limit)
    except Exception:
        limit = 50
    limit = max(1, min(500, limit))
    total = len(items)
    out = items[:limit]
    return {"ok": True, "inputs": out, "total_count": total, "returned_count": len(out), "truncated": total > len(out)}


def inputs_kind_list(args: Dict[str, Any]) -> Dict[str, Any]:
    r = obs_client.call("GetInputKindList")
    if not r.get("ok"):
        return r
    kinds = r.get("data", {}).get("inputKinds", []) or []
    return {"ok": True, "kinds": kinds, "total_count": len(kinds), "returned_count": len(kinds), "truncated": False}


def create(args: Dict[str, Any]) -> Dict[str, Any]:
    name = args.get("input_name")
    kind = args.get("input_kind")
    settings = args.get("settings") or {}
    scene_name = args.get("scene_name")
    if not isinstance(name, str) or not isinstance(kind, str):
        return {"ok": False, "error": "invalid_argument", "message": "input_name et input_kind requis"}
    safe_settings = _guard_settings_paths(settings)
    if isinstance(safe_settings, dict) and safe_settings.get("ok") is False:
        return safe_settings
    req = {"sceneName": scene_name, "inputName": name, "inputKind": kind, "inputSettings": safe_settings or {}, "sceneItemEnabled": True}
    # Supprimer sceneName si absent
    if not scene_name:
        req.pop("sceneName", None)
    r = obs_client.call("CreateInput", req)
    return r if not r.get("ok") else {"ok": True, "created": True}


def remove(args: Dict[str, Any]) -> Dict[str, Any]:
    if not args.get("confirm", False):
        return {"ok": False, "error": "confirmation_required"}
    name = args.get("input_name")
    if not isinstance(name, str):
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("RemoveInput", {"inputName": name})
    return r if not r.get("ok") else {"ok": True, "removed": True}


def rename(args: Dict[str, Any]) -> Dict[str, Any]:
    name = args.get("input_name"); new = args.get("new_name")
    if not isinstance(name, str) or not isinstance(new, str):
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("SetInputName", {"inputName": name, "newInputName": new})
    return r if not r.get("ok") else {"ok": True, "renamed": True}


def get_settings(args: Dict[str, Any]) -> Dict[str, Any]:
    name = args.get("input_name")
    if not isinstance(name, str):
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("GetInputSettings", {"inputName": name})
    return r if not r.get("ok") else {"ok": True, "settings": r.get("data", {}).get("inputSettings")}


def set_settings(args: Dict[str, Any]) -> Dict[str, Any]:
    name = args.get("input_name"); settings = args.get("settings") or {}; overlay = bool(args.get("overlay", False))
    if not isinstance(name, str) or not isinstance(settings, dict):
        return {"ok": False, "error": "invalid_argument"}
    safe_settings = _guard_settings_paths(settings)
    if isinstance(safe_settings, dict) and safe_settings.get("ok") is False:
        return safe_settings
    r = obs_client.call("SetInputSettings", {"inputName": name, "inputSettings": safe_settings or {}, "overlay": overlay})
    return r if not r.get("ok") else {"ok": True, "applied": True}


def set_mute(args: Dict[str, Any]) -> Dict[str, Any]:
    name = args.get("input_name"); muted = args.get("muted")
    if not isinstance(name, str) or not isinstance(muted, bool):
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("SetInputMute", {"inputName": name, "inputMuted": muted})
    return r if not r.get("ok") else {"ok": True, "muted": muted}


def set_volume(args: Dict[str, Any]) -> Dict[str, Any]:
    name = args.get("input_name")
    if not isinstance(name, str):
        return {"ok": False, "error": "invalid_argument"}
    req: Dict[str, Any] = {"inputName": name}
    if isinstance(args.get("volume_db"), (int, float)):
        req["inputVolumeDb"] = float(args["volume_db"])
    if isinstance(args.get("volume_mul"), (int, float)):
        req["inputVolumeMul"] = float(args["volume_mul"])
    if len(req) == 1:
        return {"ok": False, "error": "invalid_argument", "message": "volume_db ou volume_mul requis"}
    r = obs_client.call("SetInputVolume", req)
    if not r.get("ok"):
        return r
    # Lire le volume après
    gv = obs_client.call("GetInputVolume", {"inputName": name})
    if not gv.get("ok"):
        return {"ok": True}
    return {"ok": True, "volume_db": gv.get("data", {}).get("inputVolumeDb"), "volume_mul": gv.get("data", {}).get("inputVolumeMul")}


def set_monitor_type(args: Dict[str, Any]) -> Dict[str, Any]:
    name = args.get("input_name"); mtype = args.get("monitor_type")
    if not isinstance(name, str) or mtype not in {"none", "monitorOnly", "monitorAndOutput"}:
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("SetInputAudioMonitorType", {"inputName": name, "monitorType": mtype})
    return r if not r.get("ok") else {"ok": True, "applied": True}


def press_button(args: Dict[str, Any]) -> Dict[str, Any]:
    name = args.get("input_name"); button = args.get("button_name") or args.get("button")
    if not isinstance(name, str) or not isinstance(button, str):
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("PressInputPropertiesButton", {"inputName": name, "propertyName": button})
    return r if not r.get("ok") else {"ok": True, "triggered": True}
