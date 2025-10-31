import os
import json
import time
import hmac
import hashlib
import base64
import requests
from typing import Any, Dict, List, Optional, Tuple

from .utils import (
    DOCS_VIDEO_DIR,
    DOCS_IMAGES_DIR,
    ensure_dirs,
    resolve_under,
    is_url,
    file_to_base64_no_prefix,
    download_to,
    ffmpeg_thumbnail,
)

KLING_API_BASE = os.environ.get('KLING_API_BASE', 'https://api-singapore.klingai.com')
KLING_ACCESS_KEY = os.environ.get('KLING_ACCESS_KEY')
KLING_SECRET_KEY = os.environ.get('KLING_SECRET_KEY')

SESSION = requests.Session()
SESSION.headers.update({'Content-Type': 'application/json'})


class KlingApiError(RuntimeError):
    pass


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')


def _encode_jwt_hs256(ak: str, sk: str, exp_s: int = 1800) -> str:
    headers = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {"iss": ak, "exp": now + exp_s, "nbf": now - 5}
    header_b64 = _b64url(json.dumps(headers, separators=(',', ':'), ensure_ascii=False).encode('utf-8'))
    payload_b64 = _b64url(json.dumps(payload, separators=(',', ':'), ensure_ascii=False).encode('utf-8'))
    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    sig = hmac.new(sk.encode('utf-8'), signing_input, hashlib.sha256).digest()
    signature_b64 = _b64url(sig)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def _auth() -> None:
    if not (KLING_ACCESS_KEY and KLING_SECRET_KEY):
        raise KlingApiError({"status": 401, "error": {"message": "Missing KLING_ACCESS_KEY and KLING_SECRET_KEY in environment"}})
    try:
        token = _encode_jwt_hs256(KLING_ACCESS_KEY, KLING_SECRET_KEY)
    except Exception as e:
        raise KlingApiError({"status": 401, "error": {"message": f"Failed to create JWT: {e}"}})
    SESSION.headers['Authorization'] = f"Bearer {token}"


def _endpoint_for_mode(generation_mode: str) -> str:
    if generation_mode == 'text2video':
        return '/v1/videos/text2video'
    if generation_mode == 'image2video':
        return '/v1/videos/image2video'
    if generation_mode == 'multi_image2video':
        return '/v1/videos/multi-image2video'
    raise KlingApiError({"status": 400, "error": {"message": f"Unsupported generation_mode: {generation_mode}"}})


def _post_json(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    _auth()
    url = f"{KLING_API_BASE}{path}"
    r = SESSION.post(url, data=json.dumps(payload), timeout=60)
    if r.status_code >= 400:
        _raise_http_error(r)
    data = r.json()
    if not isinstance(data, dict) or data.get('code') not in (0, '0'):
        raise KlingApiError({"status": r.status_code, "error": data})
    return data


def _get_json(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _auth()
    url = f"{KLING_API_BASE}{path}"
    r = SESSION.get(url, params=params, timeout=60)
    if r.status_code >= 400:
        _raise_http_error(r)
    data = r.json()
    if not isinstance(data, dict) or data.get('code') not in (0, '0'):
        raise KlingApiError({"status": r.status_code, "error": data})
    return data


def _raise_http_error(resp: requests.Response) -> None:
    try:
        detail = resp.json()
    except Exception:
        detail = resp.text
    raise KlingApiError({"status": resp.status_code, "error": detail})


# --- Create tasks ---

def _resolve_image_field(val: str) -> str:
    if is_url(val):
        return val
    abs_path = resolve_under(DOCS_IMAGES_DIR, val)
    return file_to_base64_no_prefix(abs_path)


def create_task(generation_mode: str, params: Dict[str, Any]) -> Dict[str, Any]:
    path = _endpoint_for_mode(generation_mode)
    payload: Dict[str, Any] = {}

    # Common fields
    if 'model_name' in params:
        payload['model_name'] = params['model_name']
    if 'mode' in params:
        payload['mode'] = params['mode']
    if 'duration' in params:
        payload['duration'] = str(params['duration'])
    if 'prompt' in params:
        payload['prompt'] = params['prompt']
    if params.get('negative_prompt'):
        payload['negative_prompt'] = params['negative_prompt']
    if params.get('cfg_scale') is not None:
        payload['cfg_scale'] = params['cfg_scale']
    if params.get('callback_url'):
        payload['callback_url'] = params.get('callback_url')
    if params.get('external_task_id'):
        payload['external_task_id'] = params.get('external_task_id')

    # Camera control
    if params.get('camera_control'):
        payload['camera_control'] = params.get('camera_control')

    if generation_mode == 'text2video':
        if params.get('aspect_ratio'):
            payload['aspect_ratio'] = params['aspect_ratio']

    elif generation_mode == 'image2video':
        img = params.get('image')
        img_tail = params.get('image_tail')
        if img:
            payload['image'] = _resolve_image_field(img)
        if img_tail:
            payload['image_tail'] = _resolve_image_field(img_tail)
        if params.get('static_mask'):
            payload['static_mask'] = _resolve_image_field(params['static_mask'])
        if params.get('dynamic_masks'):
            dyn_payload: List[Dict[str, Any]] = []
            for dm in params['dynamic_masks']:
                entry: Dict[str, Any] = {}
                if 'mask' in dm:
                    entry['mask'] = _resolve_image_field(dm['mask'])
                if 'trajectories' in dm:
                    entry['trajectories'] = dm['trajectories']
                dyn_payload.append(entry)
            payload['dynamic_masks'] = dyn_payload

    elif generation_mode == 'multi_image2video':
        images = params.get('image_list') or []
        img_objs: List[Dict[str, Any]] = []
        for it in images:
            img_objs.append({"image": _resolve_image_field(it)})
        payload['image_list'] = img_objs
        if params.get('aspect_ratio'):
            payload['aspect_ratio'] = params['aspect_ratio']

    else:
        raise KlingApiError({"status": 400, "error": {"message": f"Unsupported generation_mode: {generation_mode}"}})

    return _post_json(path, payload)


# --- Status & listing ---

def get_status(generation_mode: str, task_id: Optional[str] = None, external_task_id: Optional[str] = None) -> Dict[str, Any]:
    base = _endpoint_for_mode(generation_mode)
    identifier = external_task_id or task_id
    if not identifier:
        raise KlingApiError({"status": 400, "error": {"message": "task_id or external_task_id required"}})
    path = f"{base}/{identifier}"
    return _get_json(path)


def list_tasks(generation_mode: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    base = _endpoint_for_mode(generation_mode)
    params = {"pageNum": page, "pageSize": min(max(page_size, 1), 100)}
    return _get_json(base, params=params)


# --- Download ---

def download_video(task_result: Dict[str, Any], filename: Optional[str] = None, overwrite: bool = False) -> Tuple[str, Optional[str]]:
    ensure_dirs()
    vids = (((task_result or {}).get('data') or {}).get('task_result') or {}).get('videos') or []
    if not vids:
        raise KlingApiError({"status": 404, "error": {"message": "No videos in task_result"}})
    url = vids[0].get('url')
    if not url:
        raise KlingApiError({"status": 404, "error": {"message": "Missing video url"}})

    base = filename or vids[0].get('id') or 'kling_video'
    out_name = base if base.lower().endswith('.mp4') else base + '.mp4'
    out_path = os.path.join(DOCS_VIDEO_DIR, out_name)
    if os.path.exists(out_path) and not overwrite:
        raise KlingApiError({"status": 409, "error": {"message": f"File exists: {out_path}"}})

    download_to(out_path, url)

    thumb_path = os.path.join(DOCS_IMAGES_DIR, (base + '_thumb.webp'))
    ffmpeg_thumbnail(out_path, thumb_path)

    return out_path, (os.path.isfile(thumb_path) and thumb_path or None)
