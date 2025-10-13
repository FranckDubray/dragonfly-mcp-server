import re
from typing import List, Dict, Tuple

from .fs_scanner import read_text_head

# Unified text search helper for head-limited scanning across languages
ALLOWED_EXCEPTIONS = (OSError, UnicodeDecodeError)


def search_in_file(abs_path: str, relpath: str, pattern: str, case_sensitive: bool, max_hits_per_file: int) -> List[Dict]:
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        text = read_text_head(abs_path)
    except ALLOWED_EXCEPTIONS:
        return []
    try:
        rx = re.compile(pattern, flags)
    except re.error:
        return []
    hits: List[Dict] = []
    for i, line in enumerate(text.splitlines(), start=1):
        if rx.search(line):
            hits.append({"path": relpath, "line": i})
            if len(hits) >= max_hits_per_file:
                break
    return hits
