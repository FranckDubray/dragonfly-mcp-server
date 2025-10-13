"""Office document to PDF conversion service.

Uses docx2pdf to drive native Office apps when available.
- macOS: AppleScript via Word/PowerPoint (handled by docx2pdf)
- Windows: COM automation (handled by docx2pdf)

Notes:
- Requires: pip install docx2pdf
- PowerPoint support depends on platform and Office installation.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, Any

from ..utils import get_project_root


def convert_to_pdf(input_path: str, output_path: str) -> Dict[str, Any]:
    """Convert an Office document to PDF.

    Args:
        input_path: Relative path under project root, e.g. 'docs/office/file.docx'
        output_path: Relative path under project root, e.g. 'docs/pdfs/file.pdf'

    Returns:
        Minimal result dict with input/output and duration.

    Raises:
        RuntimeError: if conversion fails or docx2pdf is not installed.
    """
    start = time.time()

    project_root = get_project_root()
    abs_in = (project_root / input_path).resolve()
    abs_out = (project_root / output_path).resolve()

    # Ensure output directory exists
    abs_out.parent.mkdir(parents=True, exist_ok=True)

    try:
        try:
            from docx2pdf import convert as docx2pdf_convert  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "docx2pdf not installed or failed to import. Install with 'pip install docx2pdf' and ensure Microsoft Office is available."
            ) from e

        # Perform conversion (doc/docx typically supported; ppt/pptx support depends on OS/Office)
        docx2pdf_convert(str(abs_in), str(abs_out))

        duration_ms = int((time.time() - start) * 1000)
        return {
            "input_path": input_path,
            "output_path": output_path,
            "duration_ms": duration_ms,
        }

    except Exception as e:
        raise RuntimeError(f"Conversion failed: {e}") from e
