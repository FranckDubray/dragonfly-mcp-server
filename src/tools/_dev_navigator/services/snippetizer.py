from typing import Tuple
import re

SECRET_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z\-_]{35}"),  # Google API key-like
    re.compile(r"sk-[A-Za-z0-9]{32,}"),     # Generic secret prefix
    re.compile(r"ghp_[A-Za-z0-9]{36,}"),    # GitHub token
]


def extract_snippet(text: str, line_no: int, context: int = 2, max_chars: int = 160) -> str:
    lines = text.splitlines()
    start = max(0, line_no - 1 - context)
    end = min(len(lines), line_no + context)
    snippet = "\n".join(lines[start:end])
    # Hard cap
    if len(snippet) > max_chars:
        snippet = snippet[: max_chars].rstrip() + "…"
    # Redact simple secrets
    for pat in SECRET_PATTERNS:
        snippet = pat.sub("[REDACTED]", snippet)
    return snippet
