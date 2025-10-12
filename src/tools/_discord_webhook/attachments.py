

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import base64
import os
import urllib.parse as up
import httpx

# Type alias for httpx multipart: (field_name, filename, content_bytes, content_type)
MultipartFile = Tuple[str, str, bytes, str]

# Discord limits
MAX_ATTACHMENT_SIZE = 25 * 1024 * 1024  # 25 MB
MAX_TOTAL_SIZE = 25 * 1024 * 1024  # 25 MB total per message


def build_files_from_attachments(attachments: List[Dict[str, Any]]) -> List[MultipartFile]:
    """
    Build multipart files from attachments with size validation.
    
    Raises:
        ValueError: If any attachment exceeds 25 MB or total exceeds 25 MB
    """
    files: List[MultipartFile] = []
    total_size = 0
    
    for idx, att in enumerate(attachments):
        filename = att.get("filename")
        b64 = att.get("content_base64")
        ctype = att.get("content_type") or "application/octet-stream"
        
        if not filename or not b64:
            raise ValueError("attachments: 'filename' and 'content_base64' are required for each item")
        
        try:
            content = base64.b64decode(b64, validate=True)
        except Exception:
            raise ValueError(f"attachments: invalid base64 for '{filename}'")
        
        # Validate individual attachment size
        size = len(content)
        if size > MAX_ATTACHMENT_SIZE:
            size_mb = size / (1024 * 1024)
            raise ValueError(f"attachments: '{filename}' is too large ({size_mb:.2f} MB). Discord limit: 25 MB per file.")
        
        total_size += size
        files.append((f"files[{idx}]", filename, content, ctype))
    
    # Validate total size
    if total_size > MAX_TOTAL_SIZE:
        total_mb = total_size / (1024 * 1024)
        raise ValueError(f"attachments: total size too large ({total_mb:.2f} MB). Discord limit: 25 MB total per message.")
    
    return files


def _guess_image_content_type(filename: str, fallback: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in (".png",):
        return "image/png"
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext in (".webp",):
        return "image/webp"
    if ext in (".gif",):
        return "image/gif"
    return fallback


def maybe_download_to_attachments(upload_image_url: Optional[str], attachments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    If attachments is empty and upload_image_url is provided, download the image and return a new single-item attachments list.
    Otherwise returns the original attachments.
    
    Raises:
        ValueError: If download fails or image exceeds 25 MB
    """
    if attachments:
        return attachments
    if not upload_image_url:
        return attachments
    
    try:
        resp = httpx.get(upload_image_url, timeout=20)
    except Exception as e:
        raise ValueError(f"upload_image_url: download failed: {e}")
    
    if resp.status_code >= 300 or resp.content is None:
        raise ValueError(f"upload_image_url: HTTP {resp.status_code}")
    
    # Validate size before encoding
    size = len(resp.content)
    if size > MAX_ATTACHMENT_SIZE:
        size_mb = size / (1024 * 1024)
        raise ValueError(f"upload_image_url: image too large ({size_mb:.2f} MB). Discord limit: 25 MB.")
    
    path = up.urlparse(upload_image_url).path
    name = os.path.basename(path) or "image"
    
    # Prefer server-declared content-type; if not an image/*, guess from extension
    ctype_hdr = resp.headers.get("content-type") or "application/octet-stream"
    ctype = ctype_hdr
    if not ctype_hdr.lower().startswith("image/"):
        ctype = _guess_image_content_type(name, ctype_hdr)
    
    b64 = base64.b64encode(resp.content).decode("ascii")
    return [{"filename": name, "content_base64": b64, "content_type": ctype}]


def inject_attachment_into_embeds(embeds: List[Dict[str, Any]], attachments: List[Dict[str, Any]], *, override: bool = False) -> None:
    """Ensure the first embed references the first attachment as its image.
    If override is False, only set the image if it is not already present.
    If override is True, always replace the image with attachment://<filename>.
    Mutates embeds in place.
    """
    if not embeds or not attachments:
        return
    first = embeds[0]
    fname = attachments[0].get("filename")
    if not fname:
        return
    if override or not first.get("image"):
        first["image"] = {"url": f"attachment://{fname}"}

 
 
