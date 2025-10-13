from typing import Dict, Any

from .constants import DEFAULT_LIMIT, MAX_LIMIT, DEFAULT_MAX_HITS_PER_FILE


def compute_effective_budgets(p: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute effective budgets and caps based on inputs and strict global policy.
    - limit: clamp to [1, MAX_LIMIT] with default DEFAULT_LIMIT
    - per-file caps: max_hits_per_file
    - scan caps: max_files_scanned, max_bytes_per_file
    """
    eff = {}
    # Page limit
    limit = p.get("limit", DEFAULT_LIMIT)
    try:
        limit = int(limit)
    except Exception:
        limit = DEFAULT_LIMIT
    if limit < 1:
        limit = 1
    if limit > MAX_LIMIT:
        limit = MAX_LIMIT
    eff["limit"] = limit

    # Per-file
    mhpf = p.get("max_hits_per_file", DEFAULT_MAX_HITS_PER_FILE)
    try:
        mhpf = int(mhpf)
    except Exception:
        mhpf = DEFAULT_MAX_HITS_PER_FILE
    if mhpf < 1:
        mhpf = 1
    if mhpf > 50:
        mhpf = 50
    eff["max_hits_per_file"] = mhpf

    # Scan caps
    mfs = p.get("max_files_scanned", 10000)
    try:
        mfs = int(mfs)
    except Exception:
        mfs = 10000
    if mfs < 100:
        mfs = 100
    if mfs > 200_000:
        mfs = 200_000
    eff["max_files_scanned"] = mfs

    mbpf = p.get("max_bytes_per_file", 65_536)
    try:
        mbpf = int(mbpf)
    except Exception:
        mbpf = 65_536
    if mbpf < 1024:
        mbpf = 1024
    if mbpf > 262_144:
        mbpf = 262_144
    eff["max_bytes_per_file"] = mbpf

    return eff
