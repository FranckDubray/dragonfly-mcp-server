from __future__ import annotations
from typing import Any, Dict
from ..services import obs_client


def take(args: Dict[str, Any], session_id: str | None, timeout_sec: int | None, dry_run: bool) -> Dict[str, Any]:
    target_type = args.get("target_type") or args.get("target")
    fmt = args.get("format", "png")
    width = args.get("width")
    height = args.get("height")
    ret = args.get("return_data", "base64")
    if target_type not in {"program", "preview", "scene", "source"}:
        return {"ok": False, "error": "invalid_argument", "message": "target_type doit être program|preview|scene|source"}
    if dry_run:
        return {"ok": True, "plan": {"target_type": target_type, "format": fmt, "width": width, "height": height, "return": ret}}

    if target_type in {"program", "preview"}:
        # Output screenshot: program=OBS_WEBSOCKET_VIDEO_OUTPUT, preview=OBS_WEBSOCKET_PREVIEW_OUTPUT (v5 utilise outputName)
        out_name = "OBS_WEBSOCKET_VIDEO_OUTPUT" if target_type == "program" else "OBS_WEBSOCKET_PREVIEW_OUTPUT"
        r = obs_client.call("GetOutputScreenshot", {"outputName": out_name, "imageFormat": fmt, "imageWidth": width, "imageHeight": height})
        if not r.get("ok"):
            return r
        return {"ok": True, "image_base64": r.get("data", {}).get("imageData")}
    else:
        # Scene ou source
        src = args.get("target_name") or args.get("scene_name") or args.get("source_name")
        if not isinstance(src, str) or not src:
            return {"ok": False, "error": "invalid_argument", "message": "target_name requis pour scene/source"}
        r = obs_client.call("GetSourceScreenshot", {"sourceName": src, "imageFormat": fmt, "imageWidth": width, "imageHeight": height})
        if not r.get("ok"):
            return r
        return {"ok": True, "image_base64": r.get("data", {}).get("imageData")}
