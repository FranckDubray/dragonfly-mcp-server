
"""
LibreOffice-based converter (headless) for Office documents to PDF.

Requires LibreOffice installed and available on PATH as 'soffice' or 'libreoffice'.
Runs in headless mode, without opening GUI windows.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any

from ..utils import get_project_root


def _find_soffice() -> str | None:
    """Return path to 'soffice' (LibreOffice) executable if available."""
    for candidate in ("soffice", "libreoffice", "soffice.exe", "libreoffice.exe"):
        path = shutil.which(candidate)
        if path:
            return path
    return None


def convert_with_libreoffice(input_path: str, output_path: str) -> Dict[str, Any]:
    """Convert using LibreOffice headless CLI.

    Args:
        input_path: Relative path under project root (docs/office/...)
        output_path: Relative path under project root (docs/pdfs/...)

    Returns:
        Dict with input/output, sizes, and duration_ms filled by caller if needed.

    Raises:
        RuntimeError: if soffice not found or conversion fails.
    """
    project_root = get_project_root()
    abs_in = (project_root / input_path).resolve()
    abs_out = (project_root / output_path).resolve()

    soffice = _find_soffice()
    if not soffice:
        raise RuntimeError("LibreOffice 'soffice' executable not found on PATH. Please install LibreOffice or adjust PATH.")

    # Ensure output directory exists
    abs_out.parent.mkdir(parents=True, exist_ok=True)

    # Run headless conversion to the output directory
    outdir = abs_out.parent

    # LibreOffice will name the PDF after the input basename (stem.pdf)
    produced = outdir / f"{abs_in.stem}.pdf"

    # Build command; --convert-to pdf works for doc(x)/ppt(x)
    cmd = [
        soffice,
        "--headless",
        "--nologo",
        "--nofirststartwizard",
        "--convert-to",
        "pdf",
        "--outdir",
        str(outdir),
        str(abs_in),
    ]

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            text=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"LibreOffice failed (code {proc.returncode}): {proc.stderr or proc.stdout}")

        if not produced.exists():
            raise RuntimeError("LibreOffice did not produce the expected PDF file.")

        # If desired output name differs, rename
        if produced.resolve() != abs_out:
            produced.replace(abs_out)

        size_bytes = abs_out.stat().st_size
        return {
            "input_path": input_path,
            "output_path": output_path,
            "output_size_bytes": size_bytes,
            "output_size_kb": round(size_bytes / 1024, 2),
            "output_size_mb": round(size_bytes / (1024 * 1024), 2),
            "message": "Conversion successful (LibreOffice)",
            "engine": "libreoffice",
        }

    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"LibreOffice conversion failed: {e}") from e
