"""HTTP download service for PDF files."""
from __future__ import annotations
from typing import Dict, Any
import requests
from pathlib import Path


def download_pdf(url: str, timeout: int = 60) -> Dict[str, Any]:
    """Download PDF from URL.
    
    Args:
        url: URL to download from
        timeout: Timeout in seconds
        
    Returns:
        Dict with 'success' (bool), 'content' (bytes), 'content_type' (str), 
        'size' (int), and 'error' (str) if failed
    """
    try:
        # Use requests with timeout and streaming
        response = requests.get(
            url,
            timeout=timeout,
            stream=True,
            allow_redirects=True,
            headers={
                'User-Agent': 'Dragonfly-MCP-Server/1.3.0 (PDF Download Tool)'
            }
        )
        
        # Check HTTP status
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"HTTP error {response.status_code}: {response.reason}"
            }
        
        # Check content type (optional, not all servers send correct MIME)
        content_type = response.headers.get('Content-Type', '').lower()
        
        # Download content
        content = response.content
        
        # Verify it's actually a PDF (magic bytes)
        if not is_pdf_content(content):
            return {
                "success": False,
                "error": "Downloaded file is not a valid PDF (magic bytes check failed)"
            }
        
        return {
            "success": True,
            "content": content,
            "content_type": content_type,
            "size": len(content)
        }
        
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": f"Download timeout after {timeout} seconds"
        }
    
    except requests.exceptions.ConnectionError as e:
        return {
            "success": False,
            "error": f"Connection error: {str(e)}"
        }
    
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Download error: {str(e)}"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


def is_pdf_content(content: bytes) -> bool:
    """Check if content is a valid PDF (magic bytes).
    
    PDF files start with %PDF-
    
    Args:
        content: File content as bytes
        
    Returns:
        True if content starts with PDF magic bytes
    """
    if not content or len(content) < 5:
        return False
    
    # Check PDF magic bytes: %PDF-
    return content[:5] == b'%PDF-'


def get_pdf_metadata(file_path: Path) -> Dict[str, Any]:
    """Extract PDF metadata (page count, etc.).
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Dict with 'pages' (int), 'title' (str), 'author' (str), etc.
        Returns empty dict on error.
    """
    try:
        # Try pypdf first (modern, recommended)
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(file_path))
            
            metadata = {
                "pages": len(reader.pages)
            }
            
            # Try to extract additional metadata if available
            if reader.metadata:
                if reader.metadata.title:
                    metadata["title"] = reader.metadata.title
                if reader.metadata.author:
                    metadata["author"] = reader.metadata.author
                if reader.metadata.subject:
                    metadata["subject"] = reader.metadata.subject
                if reader.metadata.creator:
                    metadata["creator"] = reader.metadata.creator
            
            return metadata
            
        except ImportError:
            # Fallback to PyPDF2 (older version)
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(str(file_path))
                
                metadata = {
                    "pages": len(reader.pages)
                }
                
                # Try to extract metadata
                if reader.metadata:
                    if hasattr(reader.metadata, 'title') and reader.metadata.title:
                        metadata["title"] = reader.metadata.title
                    if hasattr(reader.metadata, 'author') and reader.metadata.author:
                        metadata["author"] = reader.metadata.author
                
                return metadata
                
            except ImportError:
                # No PDF library available
                return {"pages": None, "error": "pypdf or PyPDF2 not installed"}
    
    except Exception as e:
        return {"pages": None, "error": f"Failed to read PDF metadata: {str(e)}"}


def save_pdf_to_file(content: bytes, file_path: Path) -> Dict[str, Any]:
    """Save PDF content to file.
    
    Args:
        content: PDF content as bytes
        file_path: Target file path
        
    Returns:
        Dict with 'success' (bool) and 'error' (str) if failed
    """
    try:
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return {"success": True}
        
    except PermissionError:
        return {
            "success": False,
            "error": f"Permission denied: cannot write to {file_path}"
        }
    
    except OSError as e:
        return {
            "success": False,
            "error": f"OS error writing file: {str(e)}"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error saving file: {str(e)}"
        }
