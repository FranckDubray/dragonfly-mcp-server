from typing import Dict
import re

COMMENT_PREFIXES = {
    "python": "#",
    "javascript": "//",
    "typescript": "//",
}


def _strip_block_comments(text: str, lang: str) -> str:
    if lang in {"javascript", "typescript"}:
        # Remove /* ... */ including multiline
        return re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    if lang == "html":
        # Remove <!-- ... -->
        return re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return text


def estimate_sloc(lang: str, text: str) -> int:
    if not text:
        return 0
    lang = (lang or "").lower()
    text = _strip_block_comments(text, lang)
    prefix = COMMENT_PREFIXES.get(lang)
    count = 0

    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        # Single-line comments for supported languages
        if prefix and s.startswith(prefix):
            continue
        # Heuristics by language
        if lang == "html":
            # Count non-empty lines after removing comments; keep simple
            count += 1
            continue
        if lang == "markdown":
            # Count non-empty, ignore pure code fence lines
            if s in {"```", "~~~"}:
                continue
            count += 1
            continue
        # Default path (python/js/ts)
        count += 1
    return count
