"""
File Editor Tool - S3-backed file editor with surgical editing

Edit, create, delete, compare and restore files without full rewrites.
Supports search/replace, regex, line-based operations with S3 versioning
for complete history and rollback capability.

Phase 1 Operations (standalone):
  list, create, edit, append, delete, versions, diff, restore

Phase 2 Operations (workspace — requires backend integration):
  load, unload

Example (edit):
  {
    "tool": "file_editor",
    "params": {
      "operation": "edit",
      "path": "docs/config.yaml",
      "edits": [
        {"type": "search_replace", "search": "debug: true", "replace": "debug: false"},
        {"type": "insert_after", "line": 5, "content": "# Added by editor"}
      ]
    }
  }

Example (diff):
  {
    "tool": "file_editor",
    "params": {
      "operation": "diff",
      "path": "docs/config.yaml",
      "version_a": "1771929062187",
      "version_b": "1771929085149"
    }
  }
"""
from __future__ import annotations
from typing import Dict, Any

from ._file_editor.api import route_request
from ._file_editor import spec as _spec


def run(**params) -> Dict[str, Any]:
    """Execute file editor operation.

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

    # Remove operation from params to avoid duplicate arguments
    clean_params = {k: v for k, v in params.items() if k != "operation"}

    return route_request(operation, **clean_params)


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec."""
    return _spec()
