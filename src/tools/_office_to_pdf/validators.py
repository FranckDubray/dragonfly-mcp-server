"""Input validation for office_to_pdf operations."""

import os
from pathlib import Path
from typing import Dict, Any


def get_project_root() -> Path:
    """Get project root directory."""
    cur = Path(__file__).resolve()
    while cur != cur.parent:
        if (cur / 'pyproject.toml').exists() or (cur / '.git').exists():
            return cur
        cur = cur.parent
    return Path.cwd()


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
    
    # Check chroot (must be under docs/office/)
    if not input_path.startswith("docs/office/"):
        raise ValueError(
            "Parameter 'input_path' must be under 'docs/office/' directory. "
            f"Example: 'docs/office/report.docx'"
        )
    
    # Check file extension
    valid_extensions = [".docx", ".doc", ".pptx", ".ppt"]
    file_ext = Path(input_path).suffix.lower()
    if file_ext not in valid_extensions:
        raise ValueError(
            f"Unsupported file extension '{file_ext}'. "
            f"Supported: {', '.join(valid_extensions)} (Word and PowerPoint)"
        )
    
    # Check file exists
    project_root = get_project_root()
    abs_input_path = project_root / input_path
    if not abs_input_path.exists():
        raise ValueError(f"Input file not found: {input_path}")
    
    if not abs_input_path.is_file():
        raise ValueError(f"Input path is not a file: {input_path}")
    
    # Validate output_path (optional)
    output_path = params.get("output_path", "").strip()
    if output_path:
        output_path = output_path.replace("\\", "/")
        
        # Check chroot (must be under docs/pdfs/)
        if not output_path.startswith("docs/pdfs/"):
            raise ValueError(
                "Parameter 'output_path' must be under 'docs/pdfs/' directory. "
                f"Example: 'docs/pdfs/report.pdf'"
            )
        
        # Check extension is .pdf
        if not output_path.lower().endswith(".pdf"):
            raise ValueError("Parameter 'output_path' must end with '.pdf'")
    else:
        # Auto-generate output path
        input_name = Path(input_path).stem  # filename without extension
        output_path = f"docs/pdfs/{input_name}.pdf"
    
    # Validate overwrite
    overwrite = params.get("overwrite", False)
    if not isinstance(overwrite, bool):
        raise ValueError("Parameter 'overwrite' must be a boolean")
    
    return {
        "input_path": input_path,
        "output_path": output_path,
        "overwrite": overwrite
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
    
    # Check chroot (must be under docs/office/)
    if not input_path.startswith("docs/office/"):
        raise ValueError(
            "Parameter 'input_path' must be under 'docs/office/' directory. "
            f"Example: 'docs/office/report.docx'"
        )
    
    # Check file extension
    valid_extensions = [".docx", ".doc", ".pptx", ".ppt"]
    file_ext = Path(input_path).suffix.lower()
    if file_ext not in valid_extensions:
        raise ValueError(
            f"Unsupported file extension '{file_ext}'. "
            f"Supported: {', '.join(valid_extensions)} (Word and PowerPoint)"
        )
    
    # Check file exists
    project_root = get_project_root()
    abs_input_path = project_root / input_path
    if not abs_input_path.exists():
        raise ValueError(f"Input file not found: {input_path}")
    
    if not abs_input_path.is_file():
        raise ValueError(f"Input path is not a file: {input_path}")
    
    return {
        "input_path": input_path
    }
