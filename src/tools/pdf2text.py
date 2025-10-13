"""
PDF to Text Tool - Extract text from given pages of a PDF file.
- Input: file path, optional page selection, optional limit
- Output: plain text per page and concatenated text
- Pages syntax: '1' (page1), '1-3' (1..3), '1,3,5', '2-'
- Paths are resolved from project root (pyproject/.git/src) if relative
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import json

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None

# Try flat layout first, then packaged, finally cwd fallback
try:
    from config import find_project_root
except Exception:
    try:
        from add_mcp_server.config import find_project_root
    except Exception:
        find_project_root = lambda: Path.cwd()  # type: ignore

PROJECT_ROOT = find_project_root()
_SPEC_DIR = Path(__file__).resolve().parent.parent / "tool_specs"


def _resolve(p: str) -> Path:
    q = Path(p).expanduser()
    return q if q.is_absolute() else (PROJECT_ROOT / q).resolve()


def _parse_pages(pages: str | None, total: int) -> List[int]:
    if not pages:
        return list(range(total))
    indices: List[int] = []
    pages = pages.strip()
    for part in pages.split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            a, b = part.split('-', 1)
            start = int(a) - 1 if a else 0
            end = int(b) - 1 if b else total - 1
            start = max(0, start); end = min(total - 1, end)
            if start <= end:
                indices.extend(range(start, end + 1))
        else:
            idx = int(part) - 1
            if 0 <= idx < total:
                indices.append(idx)
    # unique
    seen = set(); out: List[int] = []
    for i in indices:
        if i not in seen:
            seen.add(i); out.append(i)
    return out


def run(path: str, pages: str | None = None, limit: int = 50) -> Dict[str, Any]:
    # Validate deps
    if PdfReader is None:
        return {"success": False, "error": "pypdf is not installed. Please install pypdf>=4.2.0."}

    # Resolve path
    pdf_path = _resolve(path)
    if not pdf_path.exists() or not pdf_path.is_file():
        return {"success": False, "error": f"PDF not found: {pdf_path}"}

    # Validate limit (policy: default 50, max 500)
    try:
        limit = int(limit)
    except Exception:
        return {"success": False, "error": "limit must be an integer"}
    if limit < 1:
        limit = 1
    if limit > 500:
        limit = 500

    try:
        reader = PdfReader(str(pdf_path))
        total_pages = len(reader.pages)
        selected_indices = _parse_pages(pages, total_pages)

        total_selected = len(selected_indices)
        truncated = total_selected > limit
        if truncated:
            selected_indices = selected_indices[:limit]

        pages_text: List[Dict[str, Any]] = []
        for i in selected_indices:
            try:
                txt = reader.pages[i].extract_text() or ""
            except Exception as e:
                txt = f"<ERROR extracting page {i+1}: {e}>"
            pages_text.append({"page": i + 1, "text": txt})

        joined = "\n\n".join(p["text"] for p in pages_text)
        return {
            "success": True,
            "file": str(pdf_path),
            "total_pages": total_pages,
            "total_count": total_selected,
            "returned_count": len(pages_text),
            "truncated": truncated,
            "pages": [p["page"] for p in pages_text],
            "pages_count": len(pages_text),
            "text": joined,
            "by_page": pages_text,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def spec() -> Dict[str, Any]:
    # Load canonical spec JSON (do not duplicate schema in Python)
    spec_path = _SPEC_DIR / "pdf2text.json"
    with open(spec_path, "r", encoding="utf-8") as f:
        return json.load(f)
