"""PDF Download tool - download PDF files from URLs to docs/pdfs.

This tool provides:
- HTTP/HTTPS download with timeout control
- PDF validation (magic bytes)
- Automatic unique filename generation (no overwrites by default)
- Chroot to docs/pdfs directory for security

Example usage:
    {
        "tool": "pdf_download",
        "params": {
            "operation": "download",
            "url": "https://example.com/paper.pdf",
            "filename": "research_paper.pdf",
            "overwrite": false,
            "timeout": 60
        }
    }
"""
from __future__ import annotations
from typing import Dict, Any

# Import from the actual implementation package
from ._pdf_download.api import route_operation
from ._pdf_download import spec as _spec


def run(operation: str = "download", **params) -> Dict[str, Any]:
    """Execute pdf_download operation.
    
    Args:
        operation: Operation to perform (default: "download")
        **params: Operation parameters
        
    Returns:
        Operation result
    """
    # Normalize operation
    op = (operation or params.get("operation") or "download").strip().lower()
    
    # Validate required params for download
    if op == "download":
        url = params.get("url")
        if not url:
            return {"error": "Parameter 'url' is required for download operation"}
    
    # Route to handler
    return route_operation(op, **params)


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec.
    
    Returns:
        OpenAI function spec
    """
    return _spec()
