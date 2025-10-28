
"""Input validation for office_to_pdf operations."""

from pathlib import Path
from typing import Dict, Any

from .utils import get_project_root


def _is_within(base: Path, target: Path) -> bool:
    """Return True if target is within base (no path traversal)."""
    try:
        target.relative_to(base)
        return True
    except ValueError:
        return False


_ALLOWED_ENGINES = {"auto", "docx2pdf", "libreoffice"}


def _normalize_engine(value: Any) -> str:
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return "auto"
    if not isinstance(value, str):
        raise ValueError("Parameter 'engine' must be a string: 'auto', 'docx2pdf', or 'libreoffice'")
    v = value.strip().lower()
    if v not in _ALLOWED_ENGINES:
        raise ValueError("Parameter 'engine' must be one of: auto, docx2pdf, libreoffice")
    return v


def validate_convert_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate convert operation parameters.
    
    Args:
        params: Convert parameters
        
    Returns:
        Validated parameters
        
    Raises:
        ValueError: If validation fails
    """
    # Validate input_path
    input_path = params.get("input_path", "").strip()
    if not input_path:
        raise ValueError("Parameter 'input_path' is required and cannot be empty")
    
    # Normalize path
    input_path = input_path.replace("\\", "/")

    project_root = get_project_root()

    # Resolve absolute paths and enforce chroot under docs/office/
    in_chroot = (project_root / "docs/office").resolve()
    abs_input_path = (project_root / input_path).resolve()

    if not _is_within(in_chroot, abs_input_path):
        raise ValueError(
            "Parameter 'input_path' must be under 'docs/office/' directory (no path traversal). "
            "Example: 'docs/office/report.docx'"
        )
    
    # Check file extension
    valid_extensions = [".docx", ".doc", ".pptx", ".ppt"]
    file_ext = abs_input_path.suffix.lower()
    if file_ext not in valid_extensions:
        raise ValueError(
            f"Unsupported file extension '{file_ext}'. "
            f"Supported: {', '.join(valid_extensions)} (Word and PowerPoint)"
        )
    
    # Check file exists
    if not abs_input_path.exists():
        raise ValueError(f"Input file not found: {input_path}")
    
    if not abs_input_path.is_file():
        raise ValueError(f"Input path is not a file: {input_path}")
    
    # Validate output_path (optional)
    output_path = params.get("output_path", "").strip()
    if output_path:
        output_path = output_path.replace("\\", "/")
        abs_output_path = (project_root / output_path).resolve()
        out_chroot = (project_root / "docs/pdfs").resolve()

        # Enforce chroot for outputs
        if not _is_within(out_chroot, abs_output_path):
            raise ValueError(
                "Parameter 'output_path' must be under 'docs/pdfs/' directory (no path traversal). "
                "Example: 'docs/pdfs/report.pdf'"
            )
        
        # Check extension is .pdf
        if not str(abs_output_path).lower().endswith(".pdf"):
            raise ValueError("Parameter 'output_path' must end with '.pdf'")

        # Normalize to relative path from project root
        output_path = str(abs_output_path.relative_to(project_root))
    else:
        # Auto-generate output path
        input_name = abs_input_path.stem  # filename without extension
        output_path = f"docs/pdfs/{input_name}.pdf"
    
    # Validate overwrite
    overwrite = params.get("overwrite", False)
    if not isinstance(overwrite, bool):
        raise ValueError("Parameter 'overwrite' must be a boolean")

    # Validate engine (optional)
    engine = _normalize_engine(params.get("engine", "auto"))
    
    # Normalize input to relative path from project root
    input_path = str(abs_input_path.relative_to(project_root))

    return {
        "input_path": input_path,
        "output_path": output_path,
        "overwrite": overwrite,
        "engine": engine,
    }


def validate_get_info_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate get_info operation parameters.
    
    Args:
        params: Get info parameters
        
    Returns:
        Validated parameters
        
    Raises:
        ValueError: If validation fails
    """
    # Validate input_path (same as convert)
    input_path = params.get("input_path", "").strip()
    if not input_path:
        raise ValueError("Parameter 'input_path' is required and cannot be empty")
    
    # Normalize path
    input_path = input_path.replace("\\", "/")

    project_root = get_project_root()

    # Resolve absolute paths and enforce chroot under docs/office/
    in_chroot = (project_root / "docs/office").resolve()
    abs_input_path = (project_root / input_path).resolve()

    if not _is_within(in_chroot, abs_input_path):
        raise ValueError(
            "Parameter 'input_path' must be under 'docs/office/' directory (no path traversal). "
            "Example: 'docs/office/report.docx'"
        )
    
    # Check file extension
    valid_extensions = [".docx", ".doc", ".pptx", ".ppt"]
    file_ext = abs_input_path.suffix.lower()
    if file_ext not in valid_extensions:
        raise ValueError(
            f"Unsupported file extension '{file_ext}'. "
            f"Supported: {', '.join(valid_extensions)} (Word and PowerPoint)"
        )
    
    # Check file exists
    if not abs_input_path.exists():
        raise ValueError(f"Input file not found: {input_path}")
    
    if not abs_input_path.is_file():
        raise ValueError(f"Input path is not a file: {input_path}")
    
    return {
        "input_path": str(abs_input_path.relative_to(project_root))
    }

