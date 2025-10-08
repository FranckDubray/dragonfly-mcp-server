"""Input validation for pdf_download tool."""
from __future__ import annotations
from typing import Dict, Any
from urllib.parse import urlparse
import re


def validate_url(url: str) -> Dict[str, Any]:
    """Validate URL format and protocol.
    
    Args:
        url: URL to validate
        
    Returns:
        Dict with 'valid' (bool) and 'error' (str) if invalid
    """
    if not url or not isinstance(url, str):
        return {"valid": False, "error": "URL must be a non-empty string"}
    
    url = url.strip()
    
    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        return {"valid": False, "error": f"Invalid URL format: {e}"}
    
    # Check protocol
    if parsed.scheme not in ["http", "https"]:
        return {"valid": False, "error": f"URL must use http or https protocol (got: {parsed.scheme})"}
    
    # Check netloc (domain)
    if not parsed.netloc:
        return {"valid": False, "error": "URL must contain a valid domain"}
    
    return {"valid": True, "url": url}


def validate_filename(filename: str | None) -> Dict[str, Any]:
    """Validate and normalize filename.
    
    Args:
        filename: Optional custom filename
        
    Returns:
        Dict with 'valid' (bool), 'filename' (str), and 'error' (str) if invalid
    """
    if filename is None:
        return {"valid": True, "filename": None}
    
    if not isinstance(filename, str):
        return {"valid": False, "error": "Filename must be a string"}
    
    filename = filename.strip()
    
    if not filename:
        return {"valid": True, "filename": None}
    
    # Remove dangerous characters
    # Allow: letters, digits, spaces, dots, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9\s._-]+$', filename):
        return {
            "valid": False, 
            "error": "Filename contains invalid characters. Allowed: letters, digits, spaces, dots, hyphens, underscores"
        }
    
    # Remove path separators (security)
    if '/' in filename or '\\' in filename or '..' in filename:
        return {"valid": False, "error": "Filename cannot contain path separators (/, \\, ..)"}
    
    # Ensure .pdf extension
    if not filename.lower().endswith('.pdf'):
        filename = f"{filename}.pdf"
    
    return {"valid": True, "filename": filename}


def validate_timeout(timeout: int | None) -> Dict[str, Any]:
    """Validate timeout parameter.
    
    Args:
        timeout: Timeout in seconds
        
    Returns:
        Dict with 'valid' (bool), 'timeout' (int), and 'error' (str) if invalid
    """
    if timeout is None:
        return {"valid": True, "timeout": 60}
    
    if not isinstance(timeout, int):
        return {"valid": False, "error": "Timeout must be an integer"}
    
    if timeout < 5:
        return {"valid": False, "error": "Timeout must be at least 5 seconds"}
    
    if timeout > 300:
        return {"valid": False, "error": "Timeout cannot exceed 300 seconds (5 minutes)"}
    
    return {"valid": True, "timeout": timeout}
