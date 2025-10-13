import re
from typing import Dict, Iterable, Iterator, List, Tuple

from ...services.fs_scanner import read_text_head


def search_in_file(abs_path: str, relpath: str, pattern: str, case_sensitive: bool,
                   max_hits_per_file: int) -> List[Dict]:
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        text = read_text_head(abs_path)
    except Exception:
        return []
    hits: List[Dict] = []
    try:
        rx = re.compile(pattern, flags)
    except re.error:
        return []
    for i, line in enumerate(text.splitlines(), start=1):
        if rx.search(line):
            hits.append({"path": relpath, "line": i})
            if len(hits) >= max_hits_per_file:
                break
    return hits
