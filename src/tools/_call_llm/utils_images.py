"""
Utilities for image path normalization (docs/ chroot), file→data URL conversion,
and building OpenAI-compatible image parts. Extracted from call_llm.py to keep
files under the 7KB limit (LLM_DEV_GUIDE).
"""
from __future__ import annotations
from typing import Any, Dict, Tuple
import os
import base64
import mimetypes
from pathlib import Path

# Project root: _call_llm/ -> tools/ -> src/ -> <project>/
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DOCS = str(PROJECT_ROOT / "docs")
DOCS_ABS_ROOT = os.getenv("DOCS_ABS_ROOT", DEFAULT_DOCS)


def to_abs_docs(path: str) -> Tuple[str | None, Dict[str, Any]]:
    """Normalize an image path under DOCS_ABS_ROOT (docs chroot).
    Rules:
    - If 'path' is absolute and starts with DOCS_ABS_ROOT → accept as-is
    - If 'path' is relative and starts with 'docs/' → map to DOCS_ABS_ROOT + suffix
    - If 'path' is relative without 'docs/' → join directly under DOCS_ABS_ROOT
    Returns (full_abs | None, diag)
    diag: {input, resolved, docs_abs_root, is_abs, under_allowed, reason?}
    """
    diag: Dict[str, Any] = {
        "input": path,
        "docs_abs_root": DOCS_ABS_ROOT,
        "is_abs": False,
        "resolved": None,
        "under_allowed": False,
    }
    try:
        if not isinstance(path, str) or not path.strip():
            diag["reason"] = "empty_or_invalid_path"
            return None, diag
        p = os.path.normpath(path.strip())
        root = os.path.normpath(DOCS_ABS_ROOT)

        # Absolute under DOCS_ABS_ROOT → accept
        if os.path.isabs(p):
            diag["is_abs"] = True
            if p == root or p.startswith(root + os.sep):
                full_abs = p
            else:
                diag["reason"] = "abs_not_under_docs_root"
                diag["resolved"] = p
                return None, diag
        else:
            # Relative starting with 'docs/' → strip prefix and map
            if p == "docs" or p.startswith("docs" + os.sep):
                suffix = p[4:].lstrip(os.sep)
                full_abs = os.path.normpath(os.path.join(root, suffix)) if suffix else root
            else:
                # Relative without 'docs/' → join under DOCS_ABS_ROOT
                full_abs = os.path.normpath(os.path.join(root, p))

        diag["resolved"] = full_abs
        under = (full_abs == root) or full_abs.startswith(root + os.sep)
        diag["under_allowed"] = under
        if not under:
            diag["reason"] = "not_under_allowed_root"
            return None, diag
        return full_abs, diag
    except Exception as e:
        diag["reason"] = "exception"
        diag["exception"] = str(e)
        return None, diag


def file_to_data_url(path: str) -> Tuple[str | None, Dict[str, Any]]:
    """Read a file (under docs chroot) and return a data URL string + diagnostics."""
    diag: Dict[str, Any] = {"path": path}
    try:
        full_abs, diag_map = to_abs_docs(path)
        diag.update({"map": diag_map})
        if not full_abs:
            diag["reason"] = "mapping_failed"
            return None, diag
        diag["full_abs"] = full_abs
        # Size limit
        try:
            max_bytes = int(os.getenv("LLM_MAX_IMAGE_FILE_BYTES", "5000000"))
        except Exception:
            max_bytes = 5000000
        diag["max_bytes"] = max_bytes
        exists = os.path.exists(full_abs)
        diag["exists"] = exists
        if not exists:
            diag["reason"] = "file_not_found"
            return None, diag
        try:
            size = os.path.getsize(full_abs)
        except Exception as e:
            diag["reason"] = "getsize_failed"
            diag["exception"] = str(e)
            return None, diag
        diag["size"] = size
        if size > max_bytes:
            diag["reason"] = "too_large"
            return None, diag
        try:
            with open(full_abs, "rb") as f:
                data = f.read()
        except Exception as e:
            diag["reason"] = "open_failed"
            diag["exception"] = str(e)
            return None, diag
        mime, _ = mimetypes.guess_type(full_abs)
        diag["mime_guess"] = mime or "application/octet-stream"
        if not mime:
            mime = "application/octet-stream"
        try:
            b64 = base64.b64encode(data).decode("ascii")
        except Exception as e:
            diag["reason"] = "base64_encode_failed"
            diag["exception"] = str(e)
            return None, diag
        data_url = f"data:{mime};base64,{b64}"
        diag["ok"] = True
        return data_url, diag
    except Exception as e:
        diag["reason"] = "unexpected_exception"
        diag["exception"] = str(e)
        return None, diag


def image_part_from_url(u: str) -> Dict[str, Any]:
    """Build OpenAI-style image part from a URL/data-URL."""
    return {"type": "image_url", "image_url": {"url": u}}
