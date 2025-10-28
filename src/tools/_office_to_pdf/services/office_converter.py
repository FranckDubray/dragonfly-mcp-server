
"""
Office document to PDF conversion service.

Uses docx2pdf to drive native Office apps when available.
- macOS: AppleScript via Word/PowerPoint (handled by docx2pdf)
- Windows: COM automation (handled by docx2pdf)

Notes:
- Requires: pip install docx2pdf
- PowerPoint support depends on platform and Office installation.
- On Linux or when Office is not available, attempts a headless LibreOffice fallback (no GUI).
- You can force headless mode by setting environment variable OFFICE_TO_PDF_ENGINE=libreoffice
"""
from __future__ import annotations

import os
import platform
import time
from pathlib import Path
from typing import Dict, Any

from ..utils import get_project_root


def _try_libreoffice(input_path: str, output_path: str) -> Dict[str, Any]:
    """Attempt headless conversion via LibreOffice as a fallback."""
    from .libreoffice_converter import convert_with_libreoffice
    return convert_with_libreoffice(input_path, output_path)


def convert_to_pdf(input_path: str, output_path: str, *, engine: str = "auto") -> Dict[str, Any]:
    """Convert an Office document to PDF.

    Args:
        input_path: Relative path under project root, e.g. 'docs/office/file.docx'
        output_path: Relative path under project root, e.g. 'docs/pdfs/file.pdf'
        engine: 'auto' (default) tries docx2pdf first then falls back to LibreOffice; 'docx2pdf' forces Office; 'libreoffice' forces headless CLI.

    Returns:
        Minimal result dict with input/output and duration.

    Raises:
        RuntimeError: if conversion fails or engines are not available.
    """
    start = time.time()

    project_root = get_project_root()
    abs_in = (project_root / input_path).resolve()
    abs_out = (project_root / output_path).resolve()

    # Ensure output directory exists
    abs_out.parent.mkdir(parents=True, exist_ok=True)

    ext = abs_in.suffix.lower()
    system = platform.system()

    # Resolve engine preference: param overrides env
    env_pref = os.getenv("OFFICE_TO_PDF_ENGINE", "").strip().lower()
    if engine not in ("auto", "docx2pdf", "libreoffice"):
        engine = "auto"
    effective = engine if engine != "auto" else ("libreoffice" if env_pref == "libreoffice" else "docx2pdf")

    try:
        # If Linux + PPT, prefer LibreOffice regardless of 'docx2pdf' to avoid common failures
        if system == "Linux" and ext in (".ppt", ".pptx"):
            effective = "libreoffice" if engine != "docx2pdf" else "docx2pdf"

        result: Dict[str, Any]
        if effective == "libreoffice":
            # Try LibreOffice headless
            result = _try_libreoffice(input_path, output_path)
        else:
            # Try docx2pdf first
            try:
                from docx2pdf import convert as docx2pdf_convert  # type: ignore
                docx2pdf_convert(str(abs_in), str(abs_out))
            except Exception as e:
                if engine == "docx2pdf":
                    raise RuntimeError(
                        "Microsoft Office/docx2pdf conversion failed or is unavailable. Install Office and 'pip install docx2pdf', or try engine='libreoffice'."
                    ) from e
                # Fallback to LibreOffice in auto mode
                result = _try_libreoffice(input_path, output_path)
            else:
                # Verify output exists
                if not abs_out.exists() or not abs_out.is_file():
                    if engine == "docx2pdf":
                        raise RuntimeError(
                            "PDF file was not created by Microsoft Office. Ensure Office is installed, then retry or use engine='libreoffice'."
                        )
                    # Try fallback before giving up
                    result = _try_libreoffice(input_path, output_path)
                else:
                    size_bytes = abs_out.stat().st_size
                    result = {
                        "input_path": input_path,
                        "output_path": output_path,
                        "output_size_bytes": size_bytes,
                        "output_size_kb": round(size_bytes / 1024, 2),
                        "output_size_mb": round(size_bytes / (1024 * 1024), 2),
                        "message": "Conversion successful",
                        "engine": "docx2pdf",
                    }

        duration_ms = int((time.time() - start) * 1000)
        result["duration_ms"] = duration_ms
        return result

    except Exception as e:
        raise RuntimeError(f"Conversion failed: {e}") from e

 