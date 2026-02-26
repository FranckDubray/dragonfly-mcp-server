"""Read-only operations: list, versions, diff."""
from __future__ import annotations
from typing import Any, Dict, Optional

from . import s3_client
from .diff_engine import unified_diff, diff_stats


def op_list(
    scope: str = "user",
    prefix: str = "",
    max_keys: int = 50,
    project: Optional[str] = None,
    datasource: Optional[str] = None,
) -> Dict[str, Any]:
    """List files in a scope/prefix."""
    result = s3_client.list_objects(
        scope=scope, prefix=prefix, max_keys=max_keys,
        project=project, datasource=datasource,
    )
    if "error" in result:
        return result

    objects = result.get("objects", [])
    prefixes = result.get("prefixes", [])

    return {
        "success": True,
        "scope": scope,
        "prefix": prefix,
        "objects": objects,
        "prefixes": prefixes,
        "count": len(objects),
        "truncated": result.get("truncated", False),
    }


def op_versions(
    path: str,
    scope: str = "user",
    max_keys: int = 50,
    project: Optional[str] = None,
    datasource: Optional[str] = None,
) -> Dict[str, Any]:
    """List version history of a file."""
    result = s3_client.list_versions(
        path=path, scope=scope, max_keys=max_keys,
        project=project, datasource=datasource,
    )
    if "error" in result:
        return result

    return {
        "success": True,
        "operation": "versions",
        "path": path,
        "versions": result.get("versions", []),
        "count": result.get("count", 0),
    }


def op_diff(
    path: str,
    scope: str = "user",
    version_a: Optional[str] = None,
    version_b: Optional[str] = None,
    project: Optional[str] = None,
    datasource: Optional[str] = None,
) -> Dict[str, Any]:
    """Compare two versions of a file (unified diff)."""
    if not version_a and not version_b:
        return {"error": "At least one of 'version_a' or 'version_b' is required"}

    # Fetch version A (or current)
    obj_a = s3_client.get_object(
        path=path, scope=scope, version_id=version_a,
        project=project, datasource=datasource,
    )
    if "error" in obj_a:
        return {"error": f"Cannot fetch version_a: {obj_a['error']}"}

    # Fetch version B (or current)
    obj_b = s3_client.get_object(
        path=path, scope=scope, version_id=version_b,
        project=project, datasource=datasource,
    )
    if "error" in obj_b:
        return {"error": f"Cannot fetch version_b: {obj_b['error']}"}

    content_a = obj_a.get("body", "")
    content_b = obj_b.get("body", "")

    label_a = f"{path} (v:{version_a or 'current'})"
    label_b = f"{path} (v:{version_b or 'current'})"

    diff_text = unified_diff(content_a, content_b, label_a, label_b)
    stats = diff_stats(diff_text)

    return {
        "success": True,
        "operation": "diff",
        "path": path,
        "version_a": version_a or "current",
        "version_b": version_b or "current",
        "identical": not bool(diff_text),
        "diff": diff_text if diff_text else None,
        **stats,
    }
