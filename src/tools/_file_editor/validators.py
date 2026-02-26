"""Validators — pure validation functions for file_editor params."""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

# Scopes that are read-only (no create/edit/append/delete)
READ_ONLY_SCOPES = frozenset({"datasource"})

# Scopes that require the 'project' parameter
PROJECT_SCOPES = frozenset({"project"})

# Scopes that require the 'datasource' parameter
DATASOURCE_SCOPES = frozenset({"datasource"})

# Content-type detection by extension
MIME_MAP = {
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".json": "application/json",
    ".yaml": "text/yaml",
    ".yml": "text/yaml",
    ".xml": "application/xml",
    ".html": "text/html",
    ".htm": "text/html",
    ".css": "text/css",
    ".js": "text/javascript",
    ".ts": "text/typescript",
    ".py": "text/x-python",
    ".sh": "text/x-shellscript",
    ".csv": "text/csv",
    ".sql": "text/x-sql",
    ".env": "text/plain",
    ".toml": "text/toml",
    ".ini": "text/plain",
    ".cfg": "text/plain",
    ".log": "text/plain",
    ".rst": "text/x-rst",
    ".php": "text/x-php",
}


def validate_path(path: Optional[str]) -> Tuple[bool, str]:
    """Validate file path. Returns (ok, error_message)."""
    if not path:
        return False, "Parameter 'path' is required"
    if ".." in path:
        return False, "Path must not contain '..'"
    if "\x00" in path:
        return False, "Path must not contain null bytes"
    return True, ""


def validate_scope_writable(scope: str) -> Tuple[bool, str]:
    """Check that scope allows write operations."""
    if scope in READ_ONLY_SCOPES:
        return False, f"Scope '{scope}' is read-only"
    return True, ""


def validate_scope_params(
    scope: str, project: Optional[str], datasource: Optional[str]
) -> Tuple[bool, str]:
    """Check scope-specific required params."""
    if scope in PROJECT_SCOPES and not project:
        return False, "Parameter 'project' is required for scope 'project'"
    if scope in DATASOURCE_SCOPES and not datasource:
        return False, "Parameter 'datasource' is required for scope 'datasource'"
    return True, ""


def validate_edits(edits: Any) -> Tuple[bool, str]:
    """Basic structural validation on the edits array."""
    if not isinstance(edits, list):
        return False, "'edits' must be an array"
    if len(edits) == 0:
        return False, "'edits' must not be empty"
    for i, edit in enumerate(edits):
        if not isinstance(edit, dict):
            return False, f"Edit #{i + 1} must be an object"
        if "type" not in edit:
            return False, f"Edit #{i + 1} missing 'type'"
    return True, ""


def guess_content_type(path: str) -> str:
    """Guess MIME type from file extension."""
    for ext, mime in MIME_MAP.items():
        if path.lower().endswith(ext):
            return mime
    return "text/plain"
