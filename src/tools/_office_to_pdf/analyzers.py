
"""
Analyzers for Office files to extract metadata such as page/slide count,
count of large images (dimension >= threshold), and document properties
(author, created/modified dates, etc.).

Implementation strategy (no GUI, script-friendly):
- DOCX/PPTX (OOXML packages):
  * Parse docProps/core.xml and docProps/app.xml for metadata and counts.
  * Count embedded images >= threshold by inspecting word/media/ or ppt/media/.
  * Page count: prefer app.xml Pages (Word) or Slides (PowerPoint). If missing, try
    temporary PDF conversion then count pages.
- DOC/PPT (binary OLE):
  * Best-effort using 'olefile' if available to read SummaryInformation and
    DocumentSummaryInformation. If olefile is unavailable, metadata may be None.
  * Page count: may be present in SummaryInformation; else None (optional temp-PDF fallback).

All methods avoid driving Office GUIs.
"""
from __future__ import annotations

import io
import os
import re
import uuid
import zipfile
import datetime as _dt
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from .utils import get_project_root


# --------------------------
# Helpers
# --------------------------

def _as_iso8601(dt: Any) -> Optional[str]:
    try:
        if isinstance(dt, _dt.datetime):
            if dt.tzinfo is None:
                return dt.replace(tzinfo=_dt.timezone.utc).isoformat()
            return dt.astimezone(_dt.timezone.utc).isoformat()
        if isinstance(dt, _dt.date):
            return _dt.datetime(dt.year, dt.month, dt.day, tzinfo=_dt.timezone.utc).isoformat()
        if isinstance(dt, str):
            # Try to parse minimal ISO formats used in OOXML core/app
            # dcterms typically: 2024-10-21T14:22:01Z or with offset
            return dt
    except Exception:
        return None
    return None


def _text_or_none(elem: Optional[ET.Element]) -> Optional[str]:
    if elem is None:
        return None
    t = (elem.text or "").strip()
    return t or None


# --------------------------
# Image dimension utilities
# --------------------------

def _read_png_size(fp: io.BufferedReader) -> Optional[Tuple[int, int]]:
    sig = fp.read(8)
    if sig != b"\x89PNG\r\n\x1a\n":
        return None
    _len = fp.read(4)
    ctype = fp.read(4)
    if ctype != b"IHDR":
        return None
    width = int.from_bytes(fp.read(4), "big")
    height = int.from_bytes(fp.read(4), "big")
    return width, height


def _read_gif_size(fp: io.BufferedReader) -> Optional[Tuple[int, int]]:
    hdr = fp.read(10)
    if len(hdr) < 10 or not (hdr.startswith(b"GIF87a") or hdr.startswith(b"GIF89a")):
        return None
    width = int.from_bytes(hdr[6:8], "little")
    height = int.from_bytes(hdr[8:10], "little")
    return width, height


# JPEG size parser via SOF scan
JPEG_SOI = b"\xFF\xD8"
JPEG_MARKERS_WITH_SIZE = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}

def _read_jpeg_size(fp: io.BufferedReader) -> Optional[Tuple[int, int]]:
    if fp.read(2) != JPEG_SOI:
        return None
    while True:
        byte = fp.read(1)
        if not byte:
            return None
        if byte != b"\xFF":
            continue
        # Skip fill FFs
        while byte == b"\xFF":
            byte = fp.read(1)
        if not byte:
            return None
        marker = byte[0]
        # Standalone markers without length field
        if marker in (0x01, 0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7):
            continue
        # Read segment length
        seg_len_bytes = fp.read(2)
        if len(seg_len_bytes) < 2:
            return None
        seg_len = int.from_bytes(seg_len_bytes, "big")
        if marker in JPEG_MARKERS_WITH_SIZE:
            data = fp.read(seg_len - 2)
            if len(data) < 7:
                return None
            height = int.from_bytes(data[1:3], "big")
            width = int.from_bytes(data[3:5], "big")
            return width, height
        else:
            fp.seek(seg_len - 2, os.SEEK_CUR)


def count_large_images_in_ooxml(pkg_path: Path, threshold: Tuple[int, int] = (100, 100)) -> Optional[int]:
    """Count images with dimensions >= threshold in OOXML (docx/pptx) package.

    Returns None if the package cannot be inspected.
    """
    try:
        with zipfile.ZipFile(pkg_path) as zf:
            media_dirs = [
                "word/media/",
                "ppt/media/",
            ]
            count = 0
            for name in zf.namelist():
                if not any(name.startswith(d) for d in media_dirs):
                    continue
                try:
                    data = zf.read(name)
                except KeyError:
                    continue
                with io.BytesIO(data) as buf:
                    buf.seek(0)
                    pos = buf.tell()
                    size = _read_png_size(buf)
                    if not size:
                        buf.seek(pos)
                        size = _read_gif_size(buf)
                    if not size:
                        buf.seek(pos)
                        size = _read_jpeg_size(buf)
                    if size and size[0] >= threshold[0] and size[1] >= threshold[1]:
                        count += 1
            return count
    except Exception:
        return None


# --------------------------
# OOXML metadata (docx/pptx)
# --------------------------

def _parse_ooxml_core_props(zf: zipfile.ZipFile) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    try:
        data = zf.read("docProps/core.xml")
    except KeyError:
        return out
    try:
        root = ET.fromstring(data)
        # Namespaces often include: cp, dc, dcterms, dcmitype, xsi
        # We'll match by localname to be robust to prefixes
        def find_text(local: str) -> Optional[str]:
            for el in root.iter():
                if el.tag.rsplit('}', 1)[-1] == local:
                    t = (el.text or "").strip()
                    if t:
                        return t
            return None
        out.update({
            "title": find_text("title"),
            "subject": find_text("subject"),
            "creator": find_text("creator"),  # author
            "description": find_text("description"),
            "keywords": find_text("keywords"),
            "category": find_text("category"),
            "content_status": find_text("contentStatus"),
            "last_modified_by": find_text("lastModifiedBy"),
            "revision": find_text("revision"),
            "created_utc": _as_iso8601(find_text("created")),
            "modified_utc": _as_iso8601(find_text("modified")),
        })
    except Exception:
        return {}
    # Remove nulls
    return {k: v for k, v in out.items() if v not in (None, "")}


def _parse_ooxml_app_props(zf: zipfile.ZipFile) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    try:
        data = zf.read("docProps/app.xml")
    except KeyError:
        return out
    try:
        root = ET.fromstring(data)
        def find_text(local: str) -> Optional[str]:
            for el in root.iter():
                if el.tag.rsplit('}', 1)[-1] == local:
                    t = (el.text or "").strip()
                    if t:
                        return t
            return None
        # Numeric fields to int when possible
        def _int_or_none(s: Optional[str]) -> Optional[int]:
            try:
                return int(s) if s is not None else None
            except Exception:
                return None
        out.update({
            "application": find_text("Application"),
            "app_version": find_text("AppVersion"),
            "template": find_text("Template"),
            "company": find_text("Company"),
            "manager": find_text("Manager"),
            "pages": _int_or_none(find_text("Pages")),      # Word
            "words": _int_or_none(find_text("Words")),
            "paragraphs": _int_or_none(find_text("Paragraphs")),
            "lines": _int_or_none(find_text("Lines")),
            "slides": _int_or_none(find_text("Slides")),    # PowerPoint
            "notes": _int_or_none(find_text("Notes")),
            "hidden_slides": _int_or_none(find_text("HiddenSlides")),
            "mm_clips": _int_or_none(find_text("MMClips")),
            "total_time_minutes": _int_or_none(find_text("TotalTime")),
            "last_printed_utc": _as_iso8601(find_text("LastPrinted")),
        })
    except Exception:
        return {}
    return {k: v for k, v in out.items() if v not in (None, "")}


def extract_ooxml_properties(pkg_path: Path) -> Dict[str, Any]:
    try:
        with zipfile.ZipFile(pkg_path) as zf:
            core = _parse_ooxml_core_props(zf)
            app = _parse_ooxml_app_props(zf)
            meta = {**core, **app}
            return meta
    except Exception:
        return {}


# --------------------------
# OLE (DOC/PPT) metadata (best-effort)
# --------------------------

def extract_ole_properties(path: Path) -> Dict[str, Any]:
    try:
        import olefile  # type: ignore
    except Exception:
        return {}
    try:
        meta: Dict[str, Any] = {}
        with olefile.OleFileIO(str(path)) as ole:
            if ole.exists('\\x05SummaryInformation'):
                props = ole.getproperties('\\x05SummaryInformation')
                # Map common PIDs (see olefile docs)
                pid_map = {
                    2: 'title',
                    3: 'subject',
                    4: 'creator',  # author
                    5: 'keywords',
                    6: 'comments',
                    8: 'last_saved_by',
                    9: 'revision',
                    11: 'created_utc',
                    12: 'modified_utc',
                    13: 'print_date_utc',
                    14: 'page_count',
                    15: 'word_count',
                    16: 'char_count',
                    19: 'app_name',
                }
                for pid, name in pid_map.items():
                    val = props.get(pid)
                    if isinstance(val, (_dt.datetime, _dt.date)):
                        val = _as_iso8601(val)
                    if val not in (None, ""):
                        meta[name] = val
            if ole.exists('\\x05DocumentSummaryInformation'):
                props2 = ole.getproperties('\\x05DocumentSummaryInformation')
                pid_map2 = {
                    0x01: 'category',
                    0x02: 'presentation_target',
                    0x0E: 'company',
                    0x1F: 'manager',
                }
                for pid, name in pid_map2.items():
                    val = props2.get(pid)
                    if val not in (None, ""):
                        meta[name] = val
        return meta
    except Exception:
        return {}


# --------------------------
# Slide/page counting
# --------------------------

def count_slides_in_pptx(pkg_path: Path) -> Optional[int]:
    try:
        with zipfile.ZipFile(pkg_path) as zf:
            slides = [n for n in zf.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
            return len(slides)
    except Exception:
        return None


def _pdf_page_count(pdf_path: Path) -> Optional[int]:
    try:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except Exception:
            from pypdf import PdfReader  # type: ignore
        reader = PdfReader(str(pdf_path))
        return len(reader.pages)
    except Exception:
        try:
            data = pdf_path.read_bytes()
            return len(re.findall(br"/Type\s*/Page(?!s)\b", data))
        except Exception:
            return None


def count_pages_via_temp_pdf(input_rel: str) -> Optional[int]:
    """Attempt to convert to a temporary PDF and count its pages.

    Returns None if conversion or counting is unavailable.
    """
    try:
        from .services.office_converter import convert_to_pdf  # lazy import
    except Exception:
        return None

    project_root = get_project_root()
    tmp_dir = (project_root / "docs/pdfs/.tmp_info").resolve()
    tmp_dir.mkdir(parents=True, exist_ok=True)

    stem = Path(input_rel).stem
    tmp_pdf_rel = f"docs/pdfs/.tmp_info/{stem}_{uuid.uuid4().hex}.pdf"
    try:
        res = convert_to_pdf(input_rel, tmp_pdf_rel, engine="auto")
        abs_tmp_pdf = (project_root / res.get("output_path", tmp_pdf_rel)).resolve()
        if not abs_tmp_pdf.exists():
            return None
        pages = _pdf_page_count(abs_tmp_pdf)
        try:
            abs_tmp_pdf.unlink(missing_ok=True)  # type: ignore[arg-type]
        except Exception:
            pass
        return pages
    except Exception:
        return None


# --------------------------
# Public analyzer
# --------------------------

def analyze_office_file(input_rel: str) -> Dict[str, Any]:
    """Analyze the Office file and return metadata additions.

    Returns keys:
    - page_count: int | None
    - large_images_over_100px: int | None
    - metadata: dict (filtered, non-empty)
    """
    project_root = get_project_root()
    abs_path = (project_root / input_rel).resolve()
    ext = abs_path.suffix.lower()

    # OOXML metadata and counts
    metadata: Dict[str, Any] = {}
    if ext in (".docx", ".pptx"):
        metadata = extract_ooxml_properties(abs_path)

    # OLE metadata for legacy formats
    if ext in (".doc", ".ppt"):
        ole_meta = extract_ole_properties(abs_path)
        # Keep only non-empty keys
        metadata = {**metadata, **{k: v for k, v in ole_meta.items() if v not in (None, "")}}

    # Count large images for OOXML packages
    large_images: Optional[int] = None
    if ext in (".docx", ".pptx"):
        large_images = count_large_images_in_ooxml(abs_path, (100, 100))

    # Page/slide count
    page_count: Optional[int] = None
    if ext == ".pptx":
        page_count = metadata.get("slides") or count_slides_in_pptx(abs_path) or None
    elif ext in (".docx",):
        # Prefer Pages from app.xml if available; else temp-PDF
        page_count = metadata.get("pages") or count_pages_via_temp_pdf(input_rel)
    elif ext in (".doc", ".ppt"):
        # Try OLE property first, then temp-PDF fallback
        page_count = metadata.get("page_count") or count_pages_via_temp_pdf(input_rel)

    # Filter metadata to non-empty values only
    meta_clean = {k: v for k, v in metadata.items() if v not in (None, "")}

    return {
        "page_count": page_count,
        "large_images_over_100px": large_images,
        "metadata": meta_clean or None,
    }
