"""Workspace operations — load/unload files into LLM context.

Manifest stored at .threads/{thread_id}/workspace.json on S3.
Content is fetched live by the backend at chat-completion time.
"""
from __future__ import annotations
from typing import Any, Dict, Optional
import json
import logging
from datetime import datetime, timezone

from . import s3_client

logger = logging.getLogger(__name__)

WORKSPACE_PREFIX = ".threads"
WORKSPACE_FILENAME = "workspace.json"
WORKSPACE_MAX_SIZE = 512_000  # 500 KB


def _workspace_path(thread_id: str) -> str:
    """Build S3 path for workspace manifest."""
    safe_id = "".join(c for c in thread_id if c.isalnum() or c in ("_", "-"))
    return f"{WORKSPACE_PREFIX}/{safe_id}/{WORKSPACE_FILENAME}"


def _get_manifest(thread_id: str) -> Dict[str, Any]:
    """Fetch workspace manifest from S3. Returns empty manifest if not found."""
    path = _workspace_path(thread_id)
    obj = s3_client.get_object(path=path, scope="user")

    if "error" in obj:
        return {"thread_id": thread_id, "files": [], "total_size": 0}

    try:
        manifest = json.loads(obj.get("body", "{}"))
        if not isinstance(manifest, dict):
            manifest = {}
    except (json.JSONDecodeError, TypeError):
        manifest = {}

    manifest.setdefault("thread_id", thread_id)
    manifest.setdefault("files", [])
    manifest.setdefault("total_size", 0)
    return manifest


def _save_manifest(thread_id: str, manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Save workspace manifest to S3."""
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Recalculate total_size from file entries
    total = 0
    for f in manifest.get("files", []):
        if f.get("range"):
            total += _range_size(f["range"], f.get("total_size", 0))
        else:
            total += f.get("total_size", 0)
    manifest["total_size"] = total

    path = _workspace_path(thread_id)
    return s3_client.put_object(
        path=path,
        content=json.dumps(manifest, indent=2, ensure_ascii=False),
        scope="user",
        content_type="application/json",
    )


def _range_size(range_str: str, total: int) -> int:
    """Estimate size from a range spec."""
    if range_str.startswith("-"):
        return min(int(range_str[1:]), total)
    parts = range_str.split("-", 1)
    start = int(parts[0])
    if not parts[1]:
        return max(0, total - start)
    end = int(parts[1])
    return max(0, end - start)


# ------------------------------------------------------------------
# load
# ------------------------------------------------------------------

def op_load(
    path: str,
    scope: str = "user",
    thread_id: Optional[str] = None,
    range_: Optional[str] = None,
    project: Optional[str] = None,
    datasource: Optional[str] = None,
) -> Dict[str, Any]:
    """Load a file into the workspace manifest."""
    if not thread_id:
        return {"error": "Parameter 'thread_id' is required for load"}

    # Get file metadata to know the size
    head = s3_client.head_object(path=path, scope=scope, project=project, datasource=datasource)
    if "error" in head:
        return {"error": f"Cannot access file: {head['error']}"}

    file_size = int(head.get("size", 0))
    version_id = head.get("version_id")
    etag = head.get("etag")

    # Calculate loaded size
    loaded_size = _range_size(range_, file_size) if range_ else file_size

    # Check against workspace limit
    manifest = _get_manifest(thread_id)
    current_total = manifest.get("total_size", 0)

    # If file already loaded, subtract its old size
    for f in manifest["files"]:
        if f["path"] == path and f.get("scope", "user") == scope:
            old_size = _range_size(f["range"], f.get("total_size", 0)) if f.get("range") else f.get("total_size", 0)
            current_total -= old_size
            break

    if current_total + loaded_size > WORKSPACE_MAX_SIZE:
        return {
            "error": f"Workspace limit exceeded. Current: {current_total} bytes, "
                     f"file would add {loaded_size} bytes, limit is {WORKSPACE_MAX_SIZE} bytes.",
            "error_type": "workspace_limit",
            "hint": "Unload some files first, or use a range to load partially.",
        }

    # Update or add file entry
    file_entry = {
        "path": path,
        "scope": scope,
        "version_id": version_id,
        "etag": etag,
        "loaded_at": datetime.now(timezone.utc).isoformat(),
        "total_size": file_size,
        "range": range_,
    }

    # Replace existing entry or append
    found = False
    for i, f in enumerate(manifest["files"]):
        if f["path"] == path and f.get("scope", "user") == scope:
            manifest["files"][i] = file_entry
            found = True
            break
    if not found:
        manifest["files"].append(file_entry)

    # Save
    result = _save_manifest(thread_id, manifest)
    if "error" in result:
        return result

    logger.info("workspace.load: %s (%s, %d bytes)", path, scope, loaded_size)
    return {
        "success": True,
        "operation": "load",
        "path": path,
        "scope": scope,
        "loaded_size": loaded_size,
        "total_size": file_size,
        "range": range_,
        "version_id": version_id,
        "workspace_total": manifest["total_size"],
        "workspace_files": len(manifest["files"]),
    }


# ------------------------------------------------------------------
# unload
# ------------------------------------------------------------------

def op_unload(
    path: Optional[str] = None,
    scope: str = "user",
    thread_id: Optional[str] = None,
    all_files: bool = False,
) -> Dict[str, Any]:
    """Remove a file (or all files) from the workspace manifest."""
    if not thread_id:
        return {"error": "Parameter 'thread_id' is required for unload"}

    manifest = _get_manifest(thread_id)

    if all_files:
        removed_count = len(manifest["files"])
        manifest["files"] = []
        _save_manifest(thread_id, manifest)
        return {
            "success": True,
            "operation": "unload",
            "all": True,
            "removed_count": removed_count,
            "workspace_total": 0,
            "workspace_files": 0,
        }

    if not path:
        return {"error": "Parameter 'path' is required for unload (or use 'all: true')"}

    original_count = len(manifest["files"])
    manifest["files"] = [
        f for f in manifest["files"]
        if not (f["path"] == path and f.get("scope", "user") == scope)
    ]

    if len(manifest["files"]) == original_count:
        return {"error": f"File '{path}' (scope={scope}) not found in workspace"}

    result = _save_manifest(thread_id, manifest)
    if "error" in result:
        return result

    logger.info("workspace.unload: %s (%s)", path, scope)
    return {
        "success": True,
        "operation": "unload",
        "path": path,
        "scope": scope,
        "workspace_total": manifest["total_size"],
        "workspace_files": len(manifest["files"]),
    }
