"""Write operations: create, edit, append, delete, restore."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import logging

from . import s3_client
from .edit_engine import apply_edits, EditError
from .diff_engine import unified_diff, diff_stats
from .validators import guess_content_type

logger = logging.getLogger(__name__)


def op_create(
    path: str,
    content: str = "",
    scope: str = "user",
    content_type: Optional[str] = None,
    project: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new file."""
    if not content_type:
        content_type = guess_content_type(path)

    result = s3_client.put_object(
        path=path, content=content, scope=scope,
        content_type=content_type, project=project,
    )
    if "error" in result:
        return result

    logger.info("file_editor.create: %s (%s, %d bytes)", path, scope, len(content))
    return {
        "success": True,
        "operation": "create",
        "path": path,
        "scope": scope,
        "size": len(content),
        "version_id": result.get("version_id"),
        "content_type": content_type,
    }


def op_edit(
    path: str,
    edits: List[Dict[str, Any]],
    scope: str = "user",
    dry_run: bool = False,
    project: Optional[str] = None,
) -> Dict[str, Any]:
    """Surgical edit: fetch → transform → write back."""
    # 1. Fetch current content + etag
    obj = s3_client.get_object(path=path, scope=scope, project=project)
    if "error" in obj:
        return obj

    original = obj.get("body", "")
    etag_before = obj.get("etag")
    size_before = len(original)

    # 2. Check file size limit
    max_size = s3_client.get_max_file_size()
    if size_before > max_size:
        return {"error": f"File too large for editing ({size_before} bytes, max {max_size})"}

    # 3. Apply edits
    try:
        new_content = apply_edits(original, edits)
    except EditError as exc:
        return {"error": f"Edit failed: {exc}"}

    # 4. Generate diff
    diff_text = unified_diff(
        original, new_content,
        label_a=f"{path} (before)", label_b=f"{path} (after)",
    )
    stats = diff_stats(diff_text)

    if not diff_text:
        return {
            "success": True, "operation": "edit", "path": path,
            "changed": False, "message": "No changes resulted from the edits",
        }

    # 5. Dry run → return diff without writing
    if dry_run:
        return {
            "success": True, "operation": "edit", "path": path,
            "dry_run": True, "changed": True, "diff": diff_text, **stats,
        }

    # 6. Optimistic lock — verify etag hasn't changed
    head = s3_client.head_object(path=path, scope=scope, project=project)
    if "error" not in head and head.get("etag") != etag_before:
        return {
            "error": "Conflict: file was modified since read",
            "error_type": "conflict",
            "hint": "Retry the edit — the file was modified between read and write.",
        }

    # 7. Write back
    content_type = obj.get("content_type", "text/plain")
    if content_type == "application/octet-stream":
        content_type = guess_content_type(path)

    result = s3_client.put_object(
        path=path, content=new_content, scope=scope,
        content_type=content_type, project=project,
    )
    if "error" in result:
        return result

    logger.info("file_editor.edit: %s (%d edits applied)", path, len(edits))
    return {
        "success": True, "operation": "edit", "path": path,
        "changed": True, "diff": diff_text, **stats,
        "size_before": size_before, "size_after": len(new_content),
        "version_id": result.get("version_id"), "edits_applied": len(edits),
    }


def op_append(
    path: str,
    content: str,
    scope: str = "user",
    project: Optional[str] = None,
) -> Dict[str, Any]:
    """Append content to an existing file."""
    obj = s3_client.get_object(path=path, scope=scope, project=project)
    if "error" in obj:
        return obj

    original = obj.get("body", "")
    etag_before = obj.get("etag")

    separator = "" if original.endswith("\n") or not original else "\n"
    new_content = original + separator + content

    # Optimistic lock
    head = s3_client.head_object(path=path, scope=scope, project=project)
    if "error" not in head and head.get("etag") != etag_before:
        return {"error": "Conflict: file was modified since read", "error_type": "conflict"}

    ct = obj.get("content_type", "text/plain")
    if ct == "application/octet-stream":
        ct = guess_content_type(path)

    result = s3_client.put_object(
        path=path, content=new_content, scope=scope,
        content_type=ct, project=project,
    )
    if "error" in result:
        return result

    logger.info("file_editor.append: %s (+%d bytes)", path, len(content))
    return {
        "success": True, "operation": "append", "path": path,
        "appended_size": len(content), "total_size": len(new_content),
        "version_id": result.get("version_id"),
    }


def op_delete(
    path: str,
    scope: str = "user",
    project: Optional[str] = None,
) -> Dict[str, Any]:
    """Delete a file."""
    result = s3_client.delete_object(path=path, scope=scope, project=project)
    if "error" in result:
        return result

    logger.info("file_editor.delete: %s (%s)", path, scope)
    return {
        "success": True, "operation": "delete", "path": path,
        "scope": scope, "version_id": result.get("version_id"),
    }


def op_restore(
    path: str,
    version_id: str,
    scope: str = "user",
    project: Optional[str] = None,
) -> Dict[str, Any]:
    """Restore a file to a previous version."""
    result = s3_client.copy_object(
        src_path=path, dst_path=path,
        src_scope=scope, dst_scope=scope,
        src_version_id=version_id,
        src_project=project, dst_project=project,
    )
    if "error" in result:
        return result

    logger.info("file_editor.restore: %s → version %s", path, version_id)
    return {
        "success": True, "operation": "restore", "path": path,
        "restored_version_id": version_id,
        "new_version_id": result.get("version_id"),
    }
