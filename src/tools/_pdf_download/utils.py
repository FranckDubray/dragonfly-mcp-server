"""Utility functions for pdf_download tool."""
from __future__ import annotations
from pathlib import Path
from urllib.parse import urlparse, unquote
import os


def extract_filename_from_url(url: str) -> str:
    """Extract filename from URL.
    
    Args:
        url: URL to extract filename from
        
    Returns:
        Filename (with .pdf extension added if missing)
    """
    parsed = urlparse(url)
    path = unquote(parsed.path)  # Decode URL encoding
    
    # Get last segment
    filename = os.path.basename(path)
    
    # If empty or ends with /, use domain as base
    if not filename or filename == '/':
        domain = parsed.netloc.replace(':', '_').replace('.', '_')
        filename = f"{domain}.pdf"
    
    # Ensure .pdf extension
    if not filename.lower().endswith('.pdf'):
        filename = f"{filename}.pdf"
    
    return filename


def get_unique_filename(directory: Path, base_filename: str, overwrite: bool = False) -> str:
    """Generate unique filename in directory.
    
    If overwrite=False and file exists, appends _1, _2, etc.
    
    Args:
        directory: Target directory
        base_filename: Base filename (e.g., "document.pdf")
        overwrite: If True, returns base_filename as-is
        
    Returns:
        Unique filename (e.g., "document_1.pdf" if "document.pdf" exists)
    """
    if overwrite:
        return base_filename
    
    target_path = directory / base_filename
    
    if not target_path.exists():
        return base_filename
    
    # File exists, find unique name
    stem = base_filename[:-4]  # Remove .pdf
    counter = 1
    
    while True:
        new_filename = f"{stem}_{counter}.pdf"
        new_path = directory / new_filename
        
        if not new_path.exists():
            return new_filename
        
        counter += 1
        
        # Safety: prevent infinite loop
        if counter > 9999:
            # Use timestamp as fallback
            import time
            timestamp = int(time.time())
            return f"{stem}_{timestamp}.pdf"


def get_project_root() -> Path:
    """Get project root directory.
    
    Returns:
        Path to project root
    """
    # Assume this file is in src/tools/pdf_download/utils.py
    # Project root is 3 levels up
    current_file = Path(__file__).resolve()
    return current_file.parent.parent.parent.parent


def ensure_docs_pdfs_directory() -> Path:
    """Ensure docs/pdfs directory exists.
    
    Returns:
        Path to docs/pdfs directory
    """
    project_root = get_project_root()
    docs_pdfs = project_root / "docs" / "pdfs"
    docs_pdfs.mkdir(parents=True, exist_ok=True)
    return docs_pdfs
