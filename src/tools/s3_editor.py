"""
S3 Editor Tool - Alias of file_editor with a distinct tool name.

Same capabilities as file_editor: surgical editing, versioning, diff,
restore and workspace management — backed by the same _file_editor
implementation. Use this instance when you need two separate tool
identities registered in the MCP server.

Phase 1 Operations (standalone):
  list, create, edit, append, delete, versions, diff, restore

Phase 2 Operations (workspace — requires backend integration):
  load, unload

Example (create):
  {
    "tool": "s3_editor",
    "params": {
      "operation": "create",
      "path": "notes/hello.md",
      "content": "# Hello world"
    }
  }

Example (edit):
  {
    "tool": "s3_editor",
    "params": {
      "operation": "edit",
      "path": "notes/hello.md",
      "edits": [
        {"type": "search_replace", "search": "Hello world", "replace": "Hello Dragonfly"}
      ]
    }
  }
"""
from __future__ import annotations
from typing import Dict, Any

# Reuse 100% of the file_editor routing logic — no duplication
from ._file_editor.api import route_request
from ._s3_editor import spec as _spec


def run(**params) -> Dict[str, Any]:
    """Execute s3_editor operation.

    Args:
        **params: Operation parameters (operation, path, scope, edits, etc.)

    Returns:
        Operation result (confirmation, diff, list, error...)
    """
    operation = params.get("operation")

    if not operation:
        return {"error": "Parameter 'operation' is required"}

    valid_ops = [
        "list", "create", "edit", "append", "delete",
        "versions", "diff", "restore",
        "load", "unload",
    ]
    if operation not in valid_ops:
        return {
            "error": f"Invalid operation '{operation}'. Must be one of: {', '.join(valid_ops)}"
        }

    # Remove operation from params to avoid duplicate argument
    clean_params = {k: v for k, v in params.items() if k != "operation"}

    return route_request(operation, **clean_params)


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec."""
    return _spec()
