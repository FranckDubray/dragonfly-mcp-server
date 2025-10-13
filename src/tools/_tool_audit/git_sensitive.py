from __future__ import annotations
import subprocess
import os
from typing import Dict, List, Any

SENSITIVE_PATTERNS = (
    ".env", "\.pem$", "\.key$", "(^|/)id_rsa", "\.p12$", "\.keystore$",
    "service_account\.json$", "credentials", "token", "secrets?", "apikey", "api_key"
)


def _git_ls_files(paths: List[str]) -> List[str]:
    # Map to repo-relative and list tracked
    if not paths:
        return []
    try:
        # Use git ls-files -- to filter tracked ones
        res = subprocess.run(["git", "ls-files", "--"] + paths, capture_output=True, text=True, check=True)
        out = res.stdout.strip().splitlines()
        return [p for p in out if p]
    except Exception:
        # Fallback: assume all provided paths are tracked (best-effort)
        return paths


def scan_git_sensitive(files: List[str]) -> Dict[str, Any]:
    rel_files = []
    cwd = os.getcwd()
    for f in files:
        # make relative to repo root if possible
        try:
            rel = os.path.relpath(f, cwd)
        except Exception:
            rel = f
        rel_files.append(rel)

    tracked = _git_ls_files(rel_files)

    tracked_sensitive_files: List[str] = []
    import re
    for f in tracked:
        for pat in SENSITIVE_PATTERNS:
            if re.search(pat, f, flags=re.IGNORECASE):
                tracked_sensitive_files.append(f)
                break

    # Inline scan lightweight (only code/readme/spec)
    inline_hits: List[Dict[str, Any]] = []
    for f in tracked:
        if not os.path.isfile(f):
            continue
        if os.path.getsize(f) > 65536:
            continue
        try:
            with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                txt = fh.read()
        except Exception:
            continue
        # naive pattern and simple entropy-like check
        # mask value; we only report file-level hits with a hint
        if any(k in txt.lower() for k in ("sk-", "api_key", "token", "secret")):
            inline_hits.append({"path": f, "hint": "potential secret markers", "anchor": f"{f}#L1-L50"})

    return {
        "tracked_sensitive_files": tracked_sensitive_files[:200],
        "inline_secrets_hits": inline_hits[:200],
        "total_tracked": len(tracked),
    }
