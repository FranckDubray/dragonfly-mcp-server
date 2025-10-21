from __future__ import annotations
import re
from typing import List, Dict

_NORMALIZE_RE = re.compile(r"[^A-Za-z0-9]+")


def normalize(s: str) -> str:
    return _NORMALIZE_RE.sub("_", s).strip("_").lower()


def detect_headers(values: List[str]) -> List[str]:
    # stop at first empty header (contiguous table)
    out = []
    for v in values:
        if v is None or str(v).strip() == "":
            break
        out.append(str(v))
    return out


def build_header_maps(headers: List[str]) -> tuple[Dict[str, str], Dict[str, int]]:
    # returns: normalized_name -> real header, real header -> index (1-based)
    norm_to_real: Dict[str, str] = {}
    real_to_idx: Dict[str, int] = {}
    for i, h in enumerate(headers, start=1):
        real_to_idx[h] = i
        n = normalize(h)
        if n not in norm_to_real:
            norm_to_real[n] = h
    return norm_to_real, real_to_idx
