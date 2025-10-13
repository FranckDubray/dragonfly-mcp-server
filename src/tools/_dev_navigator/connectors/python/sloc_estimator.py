from typing import Dict, List

COMMENT_PREFIXES = {
    "python": "#",
}


def estimate_sloc(lang: str, text: str) -> int:
    prefix = COMMENT_PREFIXES.get(lang)
    count = 0
    if not text:
        return 0
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if prefix and s.startswith(prefix):
            continue
        count += 1
    return count
