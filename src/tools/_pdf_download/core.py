"""Core business logic for pdf_download tool."""
from __future__ import annotations
from typing import Dict, Any
from pathlib import Path

from .validators import validate_url, validate_filename, validate_timeout
from .utils import extract_filename_from_url, get_unique_filename, ensure_docs_pdfs_directory
from .services.downloader import download_pdf, save_pdf_to_file, get_pdf_metadata


def handle_download(
    url: str,
    filename: str | None = None,
    overwrite: bool = False,
    timeout: int = 60
) -> Dict[str, Any]:
    """Handle PDF download operation.
    
    Args:
        url: URL to download from
        filename: Optional custom filename
        overwrite: Whether to overwrite existing files
        timeout: Download timeout in seconds
        
    Returns:
        Dict with result information or error
    """
    # Validate inputs
    url_result = validate_url(url)
    if not url_result["valid"]:
        return {"error": url_result["error"]}
    
    url = url_result["url"]
    
    filename_result = validate_filename(filename)
    if not filename_result["valid"]:
        return {"error": filename_result["error"]}
    
    custom_filename = filename_result["filename"]
    
    timeout_result = validate_timeout(timeout)
    if not timeout_result["valid"]:
        return {"error": timeout_result["error"]}
    
    timeout = timeout_result["timeout"]
    
    # Determine filename
    if custom_filename:
        base_filename = custom_filename
    else:
        base_filename = extract_filename_from_url(url)
    
    # Ensure docs/pdfs directory exists
    try:
        docs_pdfs = ensure_docs_pdfs_directory()
    except Exception as e:
        return {"error": f"Failed to create docs/pdfs directory: {str(e)}"}
    
    # Get unique filename
    final_filename = get_unique_filename(docs_pdfs, base_filename, overwrite)
    target_path = docs_pdfs / final_filename
    
    # Download PDF
    download_result = download_pdf(url, timeout)
    
    if not download_result["success"]:
        return {"error": download_result["error"]}
    
    content = download_result["content"]
    size_bytes = download_result["size"]
    content_type = download_result.get("content_type", "unknown")
    
    # Save to file
    save_result = save_pdf_to_file(content, target_path)
    
    if not save_result["success"]:
        return {"error": save_result["error"]}
    
    # Extract PDF metadata (page count, etc.)
    metadata = get_pdf_metadata(target_path)
    
    # Use relative path from project root for portability
    relative_path = f"docs/pdfs/{final_filename}"
    
    # Build response
    result = {
        "success": True,
        "message": f"PDF downloaded successfully",
        "file": {
            "path": relative_path,
            "absolute_path": str(target_path),
            "filename": final_filename,
            "size_bytes": size_bytes,
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "content_type": content_type
        },
        "source": {
            "url": url,
            "timeout_used": timeout
        },
        "overwritten": overwrite and (docs_pdfs / base_filename).exists()
    }
    
    # Add metadata if available
    if metadata:
        result["metadata"] = metadata
        
        # Add page count to top level for convenience
        if "pages" in metadata and metadata["pages"] is not None:
            result["file"]["pages"] = metadata["pages"]
    
    return result
