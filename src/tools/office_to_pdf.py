"""
Office to PDF converter tool - Convert Word/PowerPoint to PDF using native Office apps

Converts Microsoft Office documents to PDF using the Office suite installed on the laptop:
- Word documents: .docx, .doc → PDF
- PowerPoint presentations: .pptx, .ppt → PDF

Uses docx2pdf library which leverages native Office applications:
- macOS: Microsoft Word/PowerPoint via AppleScript
- Windows: Microsoft Word/PowerPoint via COM automation

Requires: pip install docx2pdf
"""

from typing import Dict, Any
from ._office_to_pdf.api import route_operation
from ._office_to_pdf import spec as _spec


def run(operation: str = "convert", **params) -> Dict[str, Any]:
    """Execute office_to_pdf operation.
    
    Args:
        operation: Operation to perform (convert, get_info)
        **params: Operation parameters
        
    Returns:
        Operation result
    """
    # Normalize operation
    op = (operation or params.get("operation") or "convert").strip().lower()
    
    # Validate required params for 'convert' operation
    if op == "convert":
        if "input_path" not in params:
            return {"error": "Parameter 'input_path' is required for 'convert' operation"}
    
    # Validate required params for 'get_info' operation
    if op == "get_info":
        if "input_path" not in params:
            return {"error": "Parameter 'input_path' is required for 'get_info' operation"}
    
    # Route to handler
    return route_operation(op, **params)


def spec() -> Dict[str, Any]:
    """Return tool specification.
    
    Returns:
        OpenAI function calling spec
    """
    return _spec()
