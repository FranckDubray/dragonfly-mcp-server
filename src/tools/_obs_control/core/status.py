from __future__ import annotations
"""Status/snapshot minimal (Lot A).
"""
from typing import Any, Dict
from ..services import obs_client


def snapshot(session_id: str | None, timeout_sec: int | None) -> Dict[str, Any]:
    # Minimal: états sorties + scènes programme/preview (nom) + studio mode
    out = obs_client.call("GetStreamStatus")
    prog = obs_client.call("GetCurrentProgramScene")
    prev = obs_client.call("GetCurrentPreviewScene")
    studio = obs_client.call("GetStudioModeEnabled")
    stats = obs_client.call("GetStats")
    if not (out.get("ok") and prog.get("ok") and studio.get("ok") and stats.get("ok")):
        return {"ok": False, "error": "obs_unavailable"}
    data: Dict[str, Any] = {
        "program_scene": prog.get("data", {}).get("currentProgramSceneName"),
        "preview_scene": prev.get("data", {}).get("currentPreviewSceneName") if prev.get("ok") else None,
        "studio_mode": studio.get("data", {}).get("studioModeEnabled"),
        "outputs": {
            "stream": "active" if out.get("data", {}).get("outputActive") else ("reconnecting" if out.get("data", {}).get("outputReconnecting") else "inactive")
        },
        "stats": {
            "cpu_percent": stats.get("data", {}).get("cpuUsage"),
            "fps": stats.get("data", {}).get("activeFps"),
            "dropped_frames": stats.get("data", {}).get("outputSkippedFrames"),
            "bitrate_kbps": stats.get("data", {}).get("outputBytes", 0) * 8 / 1000.0 if isinstance(stats.get("data", {}).get("outputBytes"), (int, float)) else None,
        }
    }
    return {"ok": True, "data": data}
