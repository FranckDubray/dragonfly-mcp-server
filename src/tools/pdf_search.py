"""
PDF Search Tool - Search text inside one or multiple PDF files.
- Supports directory scanning (recursive), single file, or list of files
- Options: case sensitivity, regex mode, page ranges (string or explicit list), HARD CAP at 50 detailed results, context length
- Returns:
  - total_matches across the full scanned range (no cap)
  - up to 50 first detailed matches (file/page/snippet)
  - per-file recap and pages scanned
- Relative paths are resolved from the project root (folder with pyproject.toml/.git/src)
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple, Iterable, Optional
from pathlib import Path
import json

try:
    from config import find_project_root
except Exception:
    # Fallback: current working directory
    find_project_root = lambda: Path.cwd()  # type: ignore

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - dependency might be missing at import-time
    PdfReader = None


PROJECT_ROOT = find_project_root()
MAX_RESULTS = 50  # Hard cap of returned detailed results
_SPEC_DIR = Path(__file__).resolve().parent.parent / "tool_specs"


def _load_spec_json(name: str) -> Dict[str, Any]:
    p = _SPEC_DIR / f"{name}.json"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _resolve_target(t: str) -> Path:
    p = Path(t).expanduser()
    if not p.is_absolute():
        p = (PROJECT_ROOT / p).resolve()
    return p


def _list_pdf_files(targets: Iterable[str], recursive: bool = True) -> List[Path]:
    files: List[Path] = []
    for t in targets:
        p = _resolve_target(t)
        if p.is_file() and p.suffix.lower() == ".pdf":
            files.append(p)
        elif p.is_dir():
            if recursive:
                files.extend([q for q in p.rglob("*.pdf") if q.is_file()])
            else:
                files.extend([q for q in p.glob("*.pdf") if q.is_file()])
        else:
            continue
    # De-duplicate while preserving order
    seen = set()
    out: List[Path] = []
    for f in files:
        fr = f.resolve()
        if fr not in seen:
            seen.add(fr)
            out.append(fr)
    return out


def _parse_pages(pages: str | None, total: int) -> List[int]:
    if not pages:
        return list(range(total))
    pages = pages.strip()
    indices: List[int] = []
    for part in pages.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            try:
                start = int(a) - 1 if a else 0
                end = int(b) - 1 if b else total - 1
            except ValueError:
                continue
            start = max(0, start)
            end = min(total - 1, end)
            if start <= end:
                indices.extend(range(start, end + 1))
        else:
            try:
                idx = int(part) - 1
            except ValueError:
                continue
            if 0 <= idx < total:
                indices.append(idx)
    # unique, preserve order
    seen = set()
    out: List[int] = []
    for i in indices:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def _merge_page_selections(pages: Optional[str], pages_list: Optional[List[int]], total: int) -> List[int]:
    """Combine pages string and explicit list into a unique 0-based index list."""
    indices: List[int] = []
    if pages_list:
        for p in pages_list:
            try:
                i = int(p) - 1
            except Exception:
                continue
            if 0 <= i < total:
                indices.append(i)
    indices.extend(_parse_pages(pages, total))
    # de-duplicate preserve order
    seen = set()
    out: List[int] = []
    for i in indices:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def _find_all(text: str, query: str, *, regex: bool, case_sensitive: bool) -> List[Tuple[int, int, str]]:
    matches: List[Tuple[int, int, str]] = []
    if not text:
        return matches
    if regex:
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            pattern = re.compile(query, flags)
        except re.error:
            return matches
        for m in pattern.finditer(text):
            matches.append((m.start(), m.end(), m.group(0)))
    else:
        hay = text if case_sensitive else text.lower()
        needle = query if case_sensitive else query.lower()
        if not needle:
            return matches
        start = 0
        while True:
            pos = hay.find(needle, start)
            if pos == -1:
                break
            end = pos + len(needle)
            matches.append((pos, end, text[pos:end]))
            start = pos + 1
    return matches


def _make_snippet(text: str, start: int, end: int, ctx: int) -> str:
    a = max(0, start - ctx)
    b = min(len(text), end + ctx)
    prefix = "…" if a > 0 else ""
    suffix = "…" if b < len(text) else ""
    return prefix + text[a:b].replace("\n", " ").strip() + suffix


def run(
    operation: str = "search",
    path: str | None = None,
    paths: List[str] | None = None,
    query: str | None = None,
    pages: str | None = None,
    pages_list: Optional[List[int]] = None,
    case_sensitive: bool = False,
    regex: bool = False,
    recursive: bool = True,
    context: int = 80,
) -> Dict[str, Any]:
    """Search for a query inside PDF files.

    Behavior: returns total_matches across full scan and up to 50 first detailed results.
    """

    if operation != "search":
        return {"error": "Unknown operation: search"}

    if query is None or (isinstance(query, str) and query.strip() == ""):
        return {"error": "query is required"}

    target_list: List[str] = []
    if paths and isinstance(paths, list):
        target_list.extend([str(p) for p in paths])
    if path and isinstance(path, str):
        target_list.append(path)

    if not target_list:
        return {"error": "path or paths is required"}

    if PdfReader is None:
        return {"error": "pypdf is not installed. Please add 'pypdf' to your dependencies and install."}

    files = _list_pdf_files(target_list, recursive=recursive)
    if not files:
        return {"error": "No PDF files found for given path(s)"}

    results: List[Dict[str, Any]] = []
    per_file: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []

    total_matches = 0
    total_pages_scanned = 0

    for f in files:
        file_matches = 0
        pages_scanned_here = 0
        try:
            reader = PdfReader(str(f))
        except Exception as e:
            errors.append({"file": str(f), "error": f"Failed to open PDF: {e}"})
            continue

        total_pages = len(reader.pages)
        page_indices = _merge_page_selections(pages, pages_list, total_pages)

        for idx in page_indices:
            try:
                text = reader.pages[idx].extract_text() or ""
            except Exception as e:
                errors.append({"file": str(f), "error": f"Failed to extract text from page {idx+1}: {e}"})
                continue

            matches = _find_all(text, query, regex=regex, case_sensitive=case_sensitive)
            mcount = len(matches)
            total_matches += mcount
            file_matches += mcount

            if len(results) < MAX_RESULTS and mcount:
                for (s, e, mtxt) in matches:
                    if len(results) >= MAX_RESULTS:
                        break
                    snippet = _make_snippet(text, s, e, context)
                    results.append({
                        "file": str(f),
                        "page": idx + 1,
                        "start": s,
                        "end": e,
                        "match": mtxt,
                        "snippet": snippet,
                    })
            pages_scanned_here += 1
        per_file.append({
            "file": str(f),
            "matches": file_matches,
            "pages_scanned": pages_scanned_here,
        })
        total_pages_scanned += pages_scanned_here

    response: Dict[str, Any] = {
        "success": True,
        "query": query,
        "searched_files": len(files),
        "pages_total_scanned": total_pages_scanned,
        "total_matches": total_matches,
        "results_count": len(results),
        "results": results,
        "per_file": per_file,
        "errors": errors,
    }

    if total_matches > MAX_RESULTS:
        response["limit_reached"] = True
        response["notice"] = (
            f"Found {total_matches} matches across {total_pages_scanned} pages. "
            f"Showing first {MAX_RESULTS}. Refine your query or restrict page ranges (e.g., pages='10-20')."
        )
    else:
        response["limit_reached"] = False

    return response


def spec() -> Dict[str, Any]:
    return _load_spec_json("pdf_search")
