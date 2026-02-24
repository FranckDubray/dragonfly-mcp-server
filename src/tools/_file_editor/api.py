"""API routing layer for File Editor.

Routes each operation to the appropriate handler in core.py.
Handles top-level error catching and parameter validation.
"""
from __future__ import annotations
from typing import Any, Dict
import logging

from . import core
from .validators import (
    validate_path,
    validate_scope_writable,
    validate_scope_params,
    validate_edits,
)

logger = logging.getLogger(__name__)

# Operations that require a valid path
_PATH_REQUIRED_OPS = {
    "create", "edit", "append", "delete",
    "versions", "diff", "restore",
    "load", "unload",
}

# Operations that write (scope must not be read-only)
_WRITE_OPS = {"create", "edit", "append", "delete", "restore"}


def route_request(operation: str, **params) -> Dict[str, Any]:
    """Route an operation to its handler.

    Args:
        operation: One of the supported operations
        **params: Operation-specific parameters

    Returns:
        Result dict (always includes 'success' or 'error')
    """
    try:
        return _route(operation, **params)
    except Exception as exc:
        logger.exception("file_editor.%s failed", operation)
        return {"error": f"Unexpected error: {exc}"}


def _route(operation: str, **params) -> Dict[str, Any]:
    scope = params.get("scope", "user")
    path = params.get("path")
    project = params.get("project")
    datasource = params.get("datasource")

    # --- Path validation ---
    if operation in _PATH_REQUIRED_OPS:
        if operation == "unload" and params.get("all"):
            pass  # unload all doesn't need path
        else:
            ok, err = validate_path(path)
            if not ok:
                return {"error": err}

    # --- Scope validations ---
    # Check read-only BEFORE scope params (write on datasource → "read-only" not "missing datasource")
    if operation in _WRITE_OPS:
        ok, err = validate_scope_writable(scope)
        if not ok:
            return {"error": err}

    ok, err = validate_scope_params(scope, project, datasource)
    if not ok:
        return {"error": err}

    # --- Dispatch ---
    if operation == "list":
        return core.op_list(
            scope=scope,
            prefix=params.get("prefix", ""),
            max_keys=params.get("max_keys", 50),
            project=project,
            datasource=datasource,
        )

    if operation == "create":
        return core.op_create(
            path=path,
            content=params.get("content", ""),
            scope=scope,
            content_type=params.get("content_type"),
            project=project,
        )

    if operation == "edit":
        edits = params.get("edits")
        ok, err = validate_edits(edits)
        if not ok:
            return {"error": err}
        return core.op_edit(
            path=path,
            edits=edits,
            scope=scope,
            dry_run=params.get("dry_run", False),
            project=project,
        )

    if operation == "append":
        content = params.get("content")
        if not content:
            return {"error": "Parameter 'content' is required for append"}
        return core.op_append(
            path=path,
            content=content,
            scope=scope,
            project=project,
        )

    if operation == "delete":
        return core.op_delete(path=path, scope=scope, project=project)

    if operation == "versions":
        return core.op_versions(
            path=path,
            scope=scope,
            max_keys=params.get("max_keys", 50),
            project=project,
            datasource=datasource,
        )

    if operation == "diff":
        return core.op_diff(
            path=path,
            scope=scope,
            version_a=params.get("version_a"),
            version_b=params.get("version_b"),
            project=project,
            datasource=datasource,
        )

    if operation == "restore":
        version_id = params.get("version_id")
        if not version_id:
            return {"error": "Parameter 'version_id' is required for restore"}
        return core.op_restore(
            path=path,
            version_id=version_id,
            scope=scope,
            project=project,
        )

    # Phase 2: Workspace operations
    if operation == "load":
        from . import workspace
        return workspace.op_load(
            path=path,
            scope=scope,
            thread_id=params.get("thread_id"),
            range_=params.get("range"),
            project=project,
            datasource=datasource,
        )

    if operation == "unload":
        from . import workspace
        return workspace.op_unload(
            path=path,
            scope=scope,
            thread_id=params.get("thread_id"),
            all_files=params.get("all", False),
        )

    return {"error": f"Unknown operation '{operation}'"}
