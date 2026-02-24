"""Diff engine — unified diff between two text contents."""
from __future__ import annotations
import difflib


def unified_diff(
    content_a: str,
    content_b: str,
    label_a: str = "version_a",
    label_b: str = "version_b",
    context_lines: int = 3,
) -> str:
    """Produce a unified diff string between two contents.

    Returns empty string if contents are identical.
    """
    lines_a = content_a.splitlines(keepends=True)
    lines_b = content_b.splitlines(keepends=True)

    diff = difflib.unified_diff(
        lines_a,
        lines_b,
        fromfile=label_a,
        tofile=label_b,
        n=context_lines,
    )
    return "".join(diff)


def diff_stats(diff_text: str) -> dict:
    """Extract quick stats from a unified diff string."""
    added = 0
    removed = 0
    for line in diff_text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1

    return {"lines_added": added, "lines_removed": removed}
