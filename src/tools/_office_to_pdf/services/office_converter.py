"""Office to PDF converter using docx2pdf (native Office apps)."""

import os
from pathlib import Path
from typing import Dict, Any

try:
    from docx2pdf import convert
    DOCX2PDF_AVAILABLE = True
except ImportError:
    DOCX2PDF_AVAILABLE = False


def get_project_root() -> Path:
    """Get project root directory."""
    cur = Path(__file__).resolve()
    while cur != cur.parent:
        if (cur / 'pyproject.toml').exists() or (cur / '.git').exists():
            return cur
        cur = cur.parent
    return Path.cwd()


def convert_to_pdf(input_path: str, output_path: str) -> Dict[str, Any]:
    """Convert Office document to PDF using native Office apps.
    
    Args:
        input_path: Path to input Office file (relative to project root)
        output_path: Path to output PDF file (relative to project root)
        
    Returns:
        Dict with success status and metadata
    """
    if not DOCX2PDF_AVAILABLE:
        return {
            "success": False,
            "error": "docx2pdf library not installed. Install with: pip install docx2pdf"
        }
    
    project_root = get_project_root()
    abs_input_path = project_root / input_path
    abs_output_path = project_root / output_path
    
    # Create output directory if doesn't exist
    abs_output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Convert using docx2pdf (launches native Office app)
        convert(str(abs_input_path), str(abs_output_path))
        
        # Check output file was created
        if not abs_output_path.exists():
            return {
                "success": False,
                "error": "PDF file was not created. Check if Microsoft Office is installed and working."
            }
        
        output_size = abs_output_path.stat().st_size
        
        return {
            "success": True,
            "input_path": input_path,
            "output_path": output_path,
            "output_size_bytes": output_size,
            "output_size_kb": round(output_size / 1024, 2),
            "output_size_mb": round(output_size / (1024 * 1024), 2),
            "message": "Conversion successful"
        }
        
    except Exception as e:
        error_msg = str(e)
        
        # Provide helpful error messages
        if "word" in error_msg.lower() or "powerpoint" in error_msg.lower():
            return {
                "success": False,
                "error": f"Office application error: {error_msg}. Check if Microsoft Office (Word/PowerPoint) is installed and not running."
            }
        elif "permission" in error_msg.lower():
            return {
                "success": False,
                "error": f"Permission error: {error_msg}. Check file permissions."
            }
        else:
            return {
                "success": False,
                "error": f"Conversion error: {error_msg}"
            }
