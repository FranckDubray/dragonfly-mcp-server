import os
import mimetypes
import requests
from typing import Any, Dict, List, Tuple, Optional

from .utils import ensure_under_directory, resolve_path, has_ffmpeg, letterbox_with_ffmpeg, parse_size

OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")

DOCS_VIDEO_DIR = resolve_path("docs/video")  # videos output
DOCS_IMAGES_DIR = resolve_path("docs/images")  # images input + image assets (thumbnails/spritesheets)

SESSION = requests.Session()

SUPPORTED_SIZES = {"1280x720", "720x1280", "1792x1024", "1024x1792"}


def _ensure_auth():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY in environment.")
    SESSION.headers["Authorization"] = f"Bearer {api_key}"


def _prepare_input_reference(input_reference_path: str, size: str) -> str:
    """
    Ensure the input reference image exists under docs/images and is letterboxed to the target size
    if needed (using ffmpeg, no distortion). Returns the absolute path to the image to upload.
    """
    abs_path = ensure_under_directory(input_reference_path, DOCS_IMAGES_DIR)
    mime, _ = mimetypes.guess_type(abs_path)
    if mime not in {"image/jpeg", "image/png", "image/webp"}:
        raise ValueError("input_reference_path must be a jpeg/png/webp image under docs/images")

    # If size not supported, raise (validators restrict sizes already)
    if size not in SUPPORTED_SIZES:
        raise ValueError("Unsupported size. Must be one of: 1280x720, 720x1280, 1792x1024, 1024x1792")

    # If ffmpeg is available, letterbox to exact size in a side-by-side copy to avoid mutating source
    if has_ffmpeg():
        w, h = parse_size(size)
        base, ext = os.path.splitext(os.path.basename(abs_path))
        dst_name = f"{base}_{size}_lb{ext or '.png'}"
        dst_abs = os.path.join(DOCS_IMAGES_DIR, dst_name)
        try:
            letterbox_with_ffmpeg(abs_path, dst_abs, w, h)
            return dst_abs
        except Exception:
            # Fallback to original if ffmpeg fails (API will reject if mismatch)
            return abs_path
    else:
        # Without ffmpeg, use source as-is (API will enforce)
        return abs_path


def create_video_job(prompt: str, model: str, size: str, seconds: int, input_reference_path: Optional[str] = None) -> Dict[str, Any]:
    _ensure_auth()

    url = f"{OPENAI_API_BASE}/videos"

    files = {
        'prompt': (None, prompt),
        'model': (None, model),
        'size': (None, size),
        'seconds': (None, str(seconds)),
    }

    if input_reference_path:
        prepared = _prepare_input_reference(input_reference_path, size)
        mime, _ = mimetypes.guess_type(prepared)
        files['input_reference'] = (os.path.basename(prepared), open(prepared, 'rb'), mime)

    resp = SESSION.post(url, files=files)
    if resp.status_code >= 400:
        _raise_api_error(resp)
    return resp.json()


def get_video_status(video_id: str) -> Dict[str, Any]:
    _ensure_auth()
    url = f"{OPENAI_API_BASE}/videos/{video_id}"
    resp = SESSION.get(url)
    if resp.status_code >= 400:
        _raise_api_error(resp)
    return resp.json()


def download_video_asset(
    video_id: str,
    variant: str = "video",
    filename: Optional[str] = None,
    overwrite: bool = False,
    target_dir: Optional[str] = None,
) -> str:
    _ensure_auth()

    url = f"{OPENAI_API_BASE}/videos/{video_id}/content"
    if variant and variant != 'video':
        url += f"?variant={variant}"

    ext_map = {
        'video': '.mp4',
        'thumbnail': '.webp',
        'spritesheet': '.jpg',
    }
    ext = ext_map.get(variant, '.bin')

    if target_dir is None:
        target_dir = DOCS_VIDEO_DIR if variant == 'video' else DOCS_IMAGES_DIR

    os.makedirs(target_dir, exist_ok=True)

    if not filename:
        filename = f"{video_id}{ext}"
    elif not filename.lower().endswith(ext):
        filename += ext

    path = os.path.join(target_dir, filename)
    if os.path.exists(path) and not overwrite:
        raise FileExistsError(f"File already exists: {path}")

    with SESSION.get(url, stream=True) as r:
        if r.status_code >= 400:
            _raise_api_error(r)
        with open(path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    return path


def list_videos(limit: int = 20, after: Optional[str] = None, order: str = 'desc') -> Tuple[List[Dict[str, Any]], bool, Optional[int]]:
    _ensure_auth()
    params = {'limit': min(max(limit, 1), 100), 'order': order}
    if after:
        params['after'] = after
    url = f"{OPENAI_API_BASE}/videos"
    resp = SESSION.get(url, params=params)
    if resp.status_code >= 400:
        _raise_api_error(resp)
    data = resp.json()
    items = data if isinstance(data, list) else data.get('data') or data.get('items') or []
    total_count = data.get('total') if isinstance(data, dict) else None
    truncated = len(items) >= params['limit']
    return items, truncated, total_count


def delete_video(video_id: str) -> None:
    _ensure_auth()
    url = f"{OPENAI_API_BASE}/videos/{video_id}"
    resp = SESSION.delete(url)
    if resp.status_code >= 400:
        _raise_api_error(resp)


def remix_video(video_id: str, prompt: str) -> Dict[str, Any]:
    _ensure_auth()
    url = f"{OPENAI_API_BASE}/videos/{video_id}/remix"
    payload = {"prompt": prompt}
    headers = {"Content-Type": "application/json"}
    resp = SESSION.post(url, data=json_dumps(payload), headers=headers)
    if resp.status_code >= 400:
        _raise_api_error(resp)
    return resp.json()


def _raise_api_error(resp):
    try:
        detail = resp.json()
    except Exception:
        detail = resp.text
    status = resp.status_code
    if isinstance(detail, dict):
        raise RuntimeError({"status": status, "error": detail})
    else:
        raise RuntimeError({"status": status, "error": str(detail)[:2000]})


def json_dumps(obj) -> str:
    import json as _json
    return _json.dumps(obj, ensure_ascii=False)
