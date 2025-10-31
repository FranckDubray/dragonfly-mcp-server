import os
import time
import json
import sys
import subprocess
from typing import Any

from .core import (
    create_video_job,
    get_video_status,
    download_video_asset,
    list_videos,
    delete_video,
    remix_video,
)
from .validators import validate_params, ensure_dirs, ValidationError


def spec():
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', '..', 'tool_specs', 'openai_video.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _format_error(e: Exception) -> dict:
    if isinstance(e, ValidationError):
        return {"ok": False, "error": {"type": "validation_error", "message": str(e)}}
    if isinstance(e, RuntimeError):
        try:
            payload = e.args[0]
            if isinstance(payload, dict):
                status = payload.get("status")
                error = payload.get("error")
                return {"ok": False, "error": {"type": "api_error", "status": status, "detail": error}}
        except Exception:
            pass
        return {"ok": False, "error": {"type": "runtime_error", "message": str(e)}}
    return {"ok": False, "error": {"type": "unknown_error", "message": str(e)}}


def _auto_start_play(path: str) -> dict:
    if not path or not os.path.isfile(path):
        return {"ok": False, "error": {"type": "file_error", "message": f"File not found: {path}"}}
    try:
        if sys.platform.startswith('darwin'):
            subprocess.Popen(['open', path])
        elif os.name == 'nt':
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(['xdg-open', path])
        return {"ok": True, "path": path, "started": True}
    except Exception as e:
        return {"ok": False, "error": {"type": "launch_error", "message": str(e)}}


def run(**params) -> Any:
    try:
        ensure_dirs()
        params = validate_params(params)
        operation = params["operation"]

        if operation == "auto_start":
            # Either play a provided path or download first then play
            path = params.get('path')
            if path:
                return _auto_start_play(path)
            vid = params.get('video_id')
            if not vid:
                return {"ok": False, "error": {"type": "validation_error", "message": "video_id or path is required for auto_start"}}
            # Download to default location then open
            out = run(operation='download', video_id=vid, variant='video', filename=params.get('filename'), overwrite=params.get('overwrite', False))
            if isinstance(out, dict) and 'path' in out:
                return _auto_start_play(out['path'])
            return {"ok": False, "error": {"type": "download_error", "message": "Failed to download before auto_start"}}

        if operation == "create":
            wait = params.get("wait", False)
            max_attempts = params.get("max_attempts", 60)
            timeout_seconds = params.get("timeout_seconds", 600)
            auto_download = params.get("auto_download", False)
            auto_download_variant = params.get("auto_download_variant", "video")

            job = create_video_job(
                prompt=params["prompt"],
                model=params.get("model", "sora-2"),
                size=params.get("size", "1280x720"),
                seconds=params.get("seconds", 8),
                input_reference_path=params.get("input_reference_path"),
            )

            if not wait:
                return job

            start = time.time()
            attempts = 0
            last_status = None
            while attempts < max_attempts and (time.time() - start) < timeout_seconds:
                status = get_video_status(job["id"])  # {id, status, progress, ...}
                last_status = status
                if status.get("status") in ("completed", "failed"):
                    if status["status"] == "completed" and auto_download:
                        video_path = download_video_asset(
                            video_id=job["id"],
                            variant=auto_download_variant,
                            filename=params.get("filename"),
                        )
                        # Also download thumbnail automatically to docs/images
                        try:
                            thumb_name = (params.get("filename") or job["id"]) + "_thumb"
                            thumbnail_path = download_video_asset(
                                video_id=job["id"],
                                variant="thumbnail",
                                filename=thumb_name,
                            )
                        except Exception:
                            thumbnail_path = None
                        return {
                            "final_status": "completed",
                            "video_id": job["id"],
                            "path": video_path,
                            "thumbnail_path": thumbnail_path,
                            "variant": auto_download_variant,
                        }
                    else:
                        return {
                            "final_status": status.get("status"),
                            "video_id": job["id"],
                            "progress": last_status.get("progress"),
                        }
                attempts += 1
                remaining_time = max(0.0, timeout_seconds - (time.time() - start))
                remaining_attempts = max(1, max_attempts - attempts)
                spacing = max(1.0, remaining_time / remaining_attempts)
                time.sleep(min(spacing, 5.0))

            return {
                "final_status": "in_progress",
                "attempts_done": attempts,
                "elapsed_seconds": int(time.time() - start),
                "video_id": job["id"],
                "last_status": last_status,
                "warning": "timeout",
            }

        if operation == "get_status":
            return get_video_status(params["video_id"])

        if operation == "download":
            path = download_video_asset(
                video_id=params["video_id"],
                variant=params.get("variant", "video"),
                filename=params.get("filename"),
                overwrite=params.get("overwrite", False),
            )
            return {"path": path, "variant": params.get("variant", "video")}

        if operation == "list":
            items, truncated, total_count = list_videos(
                limit=params.get("limit", 20),
                after=params.get("after"),
                order=params.get("order", "desc"),
            )
            return {
                "items": items,
                "returned_count": len(items),
                "total_count": total_count,
                "truncated": truncated,
            }

        if operation == "delete":
            delete_video(params["video_id"])
            return {"deleted": True}

        if operation == "remix":
            wait = params.get("wait", False)
            max_attempts = params.get("max_attempts", 60)
            timeout_seconds = params.get("timeout_seconds", 600)
            auto_download = params.get("auto_download", False)
            auto_download_variant = params.get("auto_download_variant", "video")

            job = remix_video(
                video_id=params["video_id"],
                prompt=params["prompt"],
            )

            if not wait:
                return job

            start = time.time()
            attempts = 0
            last_status = None
            while attempts < max_attempts and (time.time() - start) < timeout_seconds:
                status = get_video_status(job["id"])  # {id, status, progress, ...}
                last_status = status
                if status.get("status") in ("completed", "failed"):
                    if status["status"] == "completed" and auto_download:
                        video_path = download_video_asset(
                            video_id=job["id"],
                            variant=auto_download_variant,
                            filename=params.get("filename"),
                        )
                        try:
                            thumb_name = (params.get("filename") or job["id"]) + "_thumb"
                            thumbnail_path = download_video_asset(
                                video_id=job["id"],
                                variant="thumbnail",
                                filename=thumb_name,
                            )
                        except Exception:
                            thumbnail_path = None
                        return {
                            "final_status": "completed",
                            "video_id": job["id"],
                            "path": video_path,
                            "thumbnail_path": thumbnail_path,
                            "variant": auto_download_variant,
                        }
                    else:
                        return {
                            "final_status": status.get("status"),
                            "video_id": job["id"],
                            "progress": last_status.get("progress"),
                        }
                attempts += 1
                remaining_time = max(0.0, timeout_seconds - (time.time() - start))
                remaining_attempts = max(1, max_attempts - attempts)
                spacing = max(1.0, remaining_time / remaining_attempts)
                time.sleep(min(spacing, 5.0))

            return {
                "final_status": "in_progress",
                "attempts_done": attempts,
                "elapsed_seconds": int(time.time() - start),
                "video_id": job["id"],
                "last_status": last_status,
                "warning": "timeout",
            }

        raise ValueError(f"Unsupported operation: {operation}")
    except Exception as e:
        return _format_error(e)
