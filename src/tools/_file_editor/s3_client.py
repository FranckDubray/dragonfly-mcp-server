"""S3 API client — HTTP wrapper for the Dragonfly S3 REST API."""
from __future__ import annotations
from typing import Any, Dict, Optional
import logging
import os

import requests
import urllib3

# Suppress InsecureRequestWarning when SSL verification is disabled
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
_BASE_URL = os.getenv("FILE_EDITOR_BASE_URL", "https://dev-ai.dragonflygroup.fr")
_TOKEN = os.getenv("AI_PORTAL_TOKEN", "")
_VERIFY_SSL = os.getenv("FILE_EDITOR_VERIFY_SSL", "false").lower() in ("1", "true", "yes")
_TIMEOUT = int(os.getenv("FILE_EDITOR_TIMEOUT", "30"))
_MAX_FILE_SIZE = int(os.getenv("FILE_EDITOR_MAX_FILE_SIZE", "1048576"))  # 1 MB


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {_TOKEN}",
        "Accept": "application/json",
    }


def _url(endpoint: str) -> str:
    return f"{_BASE_URL.rstrip('/')}/api/v1/s3/{endpoint}"


def _check_response(resp: requests.Response) -> Dict[str, Any]:
    """Parse response, raise on HTTP errors."""
    try:
        data = resp.json()
    except ValueError:
        data = {"body": resp.text}

    if not resp.ok:
        detail = data.get("detail") or data.get("title") or resp.text[:300]
        return {"error": f"S3 API error {resp.status_code}: {detail}", "status_code": resp.status_code}

    return data


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_objects(
    scope: str = "user",
    prefix: str = "",
    max_keys: int = 50,
    project: Optional[str] = None,
    datasource: Optional[str] = None,
) -> Dict[str, Any]:
    """List objects in a scope."""
    params: Dict[str, Any] = {"scope": scope, "prefix": prefix, "max_keys": max_keys}
    if project:
        params["project"] = project
    if datasource:
        params["datasource"] = datasource

    resp = requests.get(_url("list"), params=params, headers=_headers(),
                        verify=_VERIFY_SSL, timeout=_TIMEOUT)
    return _check_response(resp)


def get_object(
    path: str,
    scope: str = "user",
    version_id: Optional[str] = None,
    project: Optional[str] = None,
    datasource: Optional[str] = None,
) -> Dict[str, Any]:
    """Download object content as JSON-wrapped response."""
    params: Dict[str, Any] = {"scope": scope, "path": path, "json": "true"}
    if version_id:
        params["version_id"] = version_id
    if project:
        params["project"] = project
    if datasource:
        params["datasource"] = datasource

    resp = requests.get(_url("object"), params=params, headers=_headers(),
                        verify=_VERIFY_SSL, timeout=_TIMEOUT)
    return _check_response(resp)


def head_object(
    path: str,
    scope: str = "user",
    project: Optional[str] = None,
    datasource: Optional[str] = None,
) -> Dict[str, Any]:
    """Get object metadata (HEAD). Returns JSON with meta_only=true."""
    params: Dict[str, Any] = {"scope": scope, "path": path, "meta_only": "true"}
    if project:
        params["project"] = project
    if datasource:
        params["datasource"] = datasource

    resp = requests.get(_url("object"), params=params, headers=_headers(),
                        verify=_VERIFY_SSL, timeout=_TIMEOUT)
    return _check_response(resp)


def put_object(
    path: str,
    content: str,
    scope: str = "user",
    content_type: str = "text/plain",
    project: Optional[str] = None,
) -> Dict[str, Any]:
    """Upload / overwrite an object (JSON body mode)."""
    body: Dict[str, Any] = {
        "path": path,
        "content": content,
        "content_type": content_type,
        "scope": scope,
    }
    if project:
        body["project"] = project

    hdrs = _headers()
    hdrs["Content-Type"] = "application/json"

    resp = requests.post(_url("object"), json=body, headers=hdrs,
                         verify=_VERIFY_SSL, timeout=_TIMEOUT)
    return _check_response(resp)


def delete_object(
    path: str,
    scope: str = "user",
    project: Optional[str] = None,
) -> Dict[str, Any]:
    """Delete an object."""
    params: Dict[str, Any] = {"scope": scope, "path": path}
    if project:
        params["project"] = project

    resp = requests.delete(_url("object"), params=params, headers=_headers(),
                           verify=_VERIFY_SSL, timeout=_TIMEOUT)
    return _check_response(resp)


def list_versions(
    path: str,
    scope: str = "user",
    max_keys: int = 50,
    project: Optional[str] = None,
    datasource: Optional[str] = None,
) -> Dict[str, Any]:
    """List all versions of an object."""
    params: Dict[str, Any] = {"scope": scope, "path": path, "max_keys": max_keys}
    if project:
        params["project"] = project
    if datasource:
        params["datasource"] = datasource

    resp = requests.get(_url("versions"), params=params, headers=_headers(),
                        verify=_VERIFY_SSL, timeout=_TIMEOUT)
    return _check_response(resp)


def copy_object(
    src_path: str,
    dst_path: str,
    src_scope: str = "user",
    dst_scope: Optional[str] = None,
    src_version_id: Optional[str] = None,
    src_project: Optional[str] = None,
    dst_project: Optional[str] = None,
) -> Dict[str, Any]:
    """Copy an object (used for restore with src_version_id)."""
    body: Dict[str, Any] = {
        "src_scope": src_scope,
        "src_path": src_path,
        "dst_path": dst_path,
    }
    if dst_scope:
        body["dst_scope"] = dst_scope
    if src_version_id:
        body["src_version_id"] = src_version_id
    if src_project:
        body["src_project"] = src_project
    if dst_project:
        body["dst_project"] = dst_project

    hdrs = _headers()
    hdrs["Content-Type"] = "application/json"

    resp = requests.post(_url("copy"), json=body, headers=hdrs,
                         verify=_VERIFY_SSL, timeout=_TIMEOUT)
    return _check_response(resp)


def get_max_file_size() -> int:
    """Return configured max file size for editing."""
    return _MAX_FILE_SIZE
