import os
import re
from typing import Any, Dict

from .utils import resolve_path, ensure_under_directory

DOCS_VIDEOS_DIR = resolve_path("docs/video")
DOCS_IMAGES_DIR = resolve_path("docs/images")

SIZE_RE = re.compile(r"^\d{2,5}x\d{2,5}$")


class ValidationError(ValueError):
    pass


def ensure_dirs():
    os.makedirs(DOCS_VIDEOS_DIR, exist_ok=True)
    os.makedirs(DOCS_IMAGES_DIR, exist_ok=True)


def validate_params(params: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(params, dict):
        raise ValidationError("params must be an object")

    operation = params.get("operation")
    if operation not in {"create", "get_status", "download", "list", "delete", "remix", "auto_start"}:
        raise ValidationError("operation must be one of create|get_status|download|list|delete|remix|auto_start")

    # Common refs
    if operation in {"download", "get_status", "delete", "remix"}:
        video_id = params.get("video_id")
        if not video_id or not isinstance(video_id, str):
            raise ValidationError("video_id (string) is required for this operation")

    if operation == "auto_start":
        # Either a path to play or a video_id to download then play
        path = params.get("path")
        vid = params.get("video_id")
        if not path and not vid:
            raise ValidationError("auto_start requires either path or video_id")
        if path is not None and not isinstance(path, str):
            raise ValidationError("path must be a string if provided")

    if operation == "create":
        prompt = params.get("prompt")
        if not prompt or not isinstance(prompt, str):
            raise ValidationError("prompt (string) is required for create")

        model = params.get("model", "sora-2")
        if model not in {"sora-2", "sora-2-pro"}:
            raise ValidationError("model must be sora-2 or sora-2-pro")

        size = params.get("size", "1280x720")
        if not isinstance(size, str) or not SIZE_RE.match(size):
            raise ValidationError("size must match pattern WxH, e.g., 1280x720")

        seconds = params.get("seconds", 8)
        if not isinstance(seconds, int) or not (1 <= seconds <= 60):
            raise ValidationError("seconds must be an integer between 1 and 60")

        input_reference_path = params.get("input_reference_path")
        if input_reference_path is not None:
            if not isinstance(input_reference_path, str):
                raise ValidationError("input_reference_path must be a string path under docs/images")
            abs_path = ensure_under_directory(input_reference_path, DOCS_IMAGES_DIR)
            if not os.path.isfile(abs_path):
                raise ValidationError("input_reference_path must exist under docs/images")
            if not _is_allowed_image(abs_path):
                raise ValidationError("input_reference_path must be jpeg/png/webp")

        # Wait orchestration
        wait = params.get("wait", False)
        if wait:
            max_attempts = params.get("max_attempts", 60)
            timeout_seconds = params.get("timeout_seconds", 600)
            if not (isinstance(max_attempts, int) and 1 <= max_attempts <= 600):
                raise ValidationError("max_attempts must be an integer between 1 and 600")
            if not (isinstance(timeout_seconds, int) and 1 <= timeout_seconds <= 3600):
                raise ValidationError("timeout_seconds must be an integer between 1 and 3600")

        # Auto download
        auto_download = params.get("auto_download", False)
        if auto_download:
            adv = params.get("auto_download_variant", "video")
            if adv not in {"video", "thumbnail", "spritesheet"}:
                raise ValidationError("auto_download_variant must be video|thumbnail|spritesheet")
            filename = params.get("filename")
            if filename is not None and not isinstance(filename, str):
                raise ValidationError("filename must be a string if provided")

    elif operation == "download":
        variant = params.get("variant", "video")
        if variant not in {"video", "thumbnail", "spritesheet"}:
            raise ValidationError("variant must be one of video|thumbnail|spritesheet")
        filename = params.get("filename")
        if filename is not None and not isinstance(filename, str):
            raise ValidationError("filename must be a string if provided")
        overwrite = params.get("overwrite", False)
        if not isinstance(overwrite, bool):
            raise ValidationError("overwrite must be a boolean")

    elif operation == "list":
        limit = params.get("limit", 20)
        if not (isinstance(limit, int) and 1 <= limit <= 100):
            raise ValidationError("limit must be an integer between 1 and 100")
        order = params.get("order", "desc")
        if order not in {"asc", "desc"}:
            raise ValidationError("order must be asc or desc")

    elif operation == "remix":
        prompt = params.get("prompt")
        if not prompt or not isinstance(prompt, str):
            raise ValidationError("prompt (string) is required for remix")

    return params


def _is_allowed_image(path: str) -> bool:
    low = path.lower()
    return low.endswith('.jpg') or low.endswith('.jpeg') or low.endswith('.png') or low.endswith('.webp')
