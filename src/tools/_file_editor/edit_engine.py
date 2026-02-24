"""Edit engine — apply surgical edits to text content.

Supports: search_replace, regex_replace, insert_after, insert_before,
delete_lines, replace_lines.  All edits are applied sequentially to
produce a single new version (atomic batch).
"""
from __future__ import annotations
from typing import Any, Dict, List
import re


class EditError(Exception):
    """Raised when an edit operation fails."""


def apply_edits(content: str, edits: List[Dict[str, Any]]) -> str:
    """Apply a list of edits sequentially to *content*.

    Raises EditError on invalid edit or target not found.
    Returns the transformed content.
    """
    for idx, edit in enumerate(edits):
        edit_type = edit.get("type")
        try:
            if edit_type == "search_replace":
                content = _search_replace(content, edit)
            elif edit_type == "regex_replace":
                content = _regex_replace(content, edit)
            elif edit_type == "insert_after":
                content = _insert_after(content, edit)
            elif edit_type == "insert_before":
                content = _insert_before(content, edit)
            elif edit_type == "delete_lines":
                content = _delete_lines(content, edit)
            elif edit_type == "replace_lines":
                content = _replace_lines(content, edit)
            else:
                raise EditError(f"Unknown edit type '{edit_type}'")
        except EditError:
            raise
        except Exception as exc:
            raise EditError(f"Edit #{idx + 1} ({edit_type}) failed: {exc}") from exc

    return content


# ------------------------------------------------------------------
# Edit implementations
# ------------------------------------------------------------------

def _search_replace(content: str, edit: Dict[str, Any]) -> str:
    search = edit.get("search")
    replace = edit.get("replace", "")
    occurrence = edit.get("occurrence", 0)

    if not search:
        raise EditError("search_replace requires 'search'")

    if search not in content:
        raise EditError(
            f"search_replace: string not found: {search[:80]!r}"
        )

    if occurrence == 0:
        # Replace all
        return content.replace(search, replace)

    # Replace specific occurrence
    parts = content.split(search)
    if occurrence > len(parts) - 1:
        raise EditError(
            f"search_replace: occurrence {occurrence} not found "
            f"(only {len(parts) - 1} found)"
        )

    result_parts = []
    for i, part in enumerate(parts):
        result_parts.append(part)
        if i < len(parts) - 1:
            result_parts.append(replace if i + 1 == occurrence else search)

    return "".join(result_parts)


def _regex_replace(content: str, edit: Dict[str, Any]) -> str:
    pattern = edit.get("search")
    replace = edit.get("replace", "")

    if not pattern:
        raise EditError("regex_replace requires 'search' (regex pattern)")

    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        raise EditError(f"regex_replace: invalid pattern: {exc}") from exc

    new_content, count = compiled.subn(replace, content)
    if count == 0:
        raise EditError(f"regex_replace: pattern matched nothing: {pattern!r}")

    return new_content


def _insert_after(content: str, edit: Dict[str, Any]) -> str:
    line_no = edit.get("line")
    insert_content = edit.get("content", "")

    if line_no is None:
        raise EditError("insert_after requires 'line'")

    lines = content.split("\n")
    if line_no < 1 or line_no > len(lines):
        raise EditError(f"insert_after: line {line_no} out of range (1-{len(lines)})")

    insert_lines = insert_content.split("\n")
    lines[line_no:line_no] = insert_lines
    return "\n".join(lines)


def _insert_before(content: str, edit: Dict[str, Any]) -> str:
    line_no = edit.get("line")
    insert_content = edit.get("content", "")

    if line_no is None:
        raise EditError("insert_before requires 'line'")

    lines = content.split("\n")
    if line_no < 1 or line_no > len(lines):
        raise EditError(f"insert_before: line {line_no} out of range (1-{len(lines)})")

    insert_lines = insert_content.split("\n")
    idx = line_no - 1
    lines[idx:idx] = insert_lines
    return "\n".join(lines)


def _delete_lines(content: str, edit: Dict[str, Any]) -> str:
    start = edit.get("start_line")
    end = edit.get("end_line")

    if start is None or end is None:
        raise EditError("delete_lines requires 'start_line' and 'end_line'")

    lines = content.split("\n")
    _validate_range(start, end, len(lines), "delete_lines")

    del lines[start - 1:end]
    return "\n".join(lines)


def _replace_lines(content: str, edit: Dict[str, Any]) -> str:
    start = edit.get("start_line")
    end = edit.get("end_line")
    new_content = edit.get("content", "")

    if start is None or end is None:
        raise EditError("replace_lines requires 'start_line' and 'end_line'")

    lines = content.split("\n")
    _validate_range(start, end, len(lines), "replace_lines")

    replacement = new_content.split("\n")
    lines[start - 1:end] = replacement
    return "\n".join(lines)


def _validate_range(start: int, end: int, total: int, op: str) -> None:
    if start < 1:
        raise EditError(f"{op}: start_line must be >= 1")
    if end < start:
        raise EditError(f"{op}: end_line ({end}) < start_line ({start})")
    if start > total:
        raise EditError(f"{op}: start_line {start} out of range (1-{total})")
    if end > total:
        raise EditError(f"{op}: end_line {end} out of range (1-{total})")
