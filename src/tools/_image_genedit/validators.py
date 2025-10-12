"""
Image input validation and normalization.
Converts all inputs (http(s), local files, data URLs, raw base64) to data URLs for consistent processing.
"""
from typing import List, Optional, Tuple
from pathlib import Path
import base64
import os
import mimetypes
import logging

from .utils import download_to_data_url

logger = logging.getLogger(__name__)


def _get_docs_root() -> Path:
    """
    Get absolute path to ./docs directory.
    Uses intelligent project root detection (same as call_llm).
    """
    # Try env var override first
    docs_abs = os.getenv("DOCS_ABS_ROOT", "").strip()
    if docs_abs:
        p = Path(docs_abs)
        if p.is_dir():
            return p
    
    # Fallback: project root detection
    # validators.py is in src/tools/_image_genedit/
    # Project root is 3 levels up
    here = Path(__file__).resolve()
    project_root = here.parent.parent.parent.parent
    docs_dir = project_root / "docs"
    
    if docs_dir.is_dir():
        return docs_dir
    
    # Last resort: current working directory
    return Path.cwd() / "docs"


def load_local_images(file_paths: List[str]) -> Tuple[List[str], Optional[str]]:
    """
    Load local image files from ./docs and convert to data URLs.
    
    Args:
        file_paths: List of relative paths (relative to ./docs)
    
    Returns:
        (data_urls_list, error_message)
    
    Examples:
        - "test.png" → ./docs/test.png
        - "images/photo.jpg" → ./docs/images/photo.jpg
        - "subdir/image.webp" → ./docs/subdir/image.webp
    """
    if not file_paths:
        return [], None
    
    docs_root = _get_docs_root()
    data_urls: List[str] = []
    errors: List[str] = []
    
    logger.info(f"Loading {len(file_paths)} local image(s) from ./docs")
    
    for fp in file_paths:
        if not isinstance(fp, str):
            continue
        
        fp = fp.strip()
        if not fp:
            continue
        
        # Build absolute path (resolve to prevent directory traversal)
        try:
            full_path = (docs_root / fp).resolve()
            
            # Security: ensure path is still under docs_root
            if not str(full_path).startswith(str(docs_root.resolve())):
                logger.warning(f"Path traversal denied: {fp}")
                errors.append(f"{fp}: path traversal denied")
                continue
            
            if not full_path.is_file():
                logger.warning(f"File not found: {fp}")
                errors.append(f"{fp}: file not found in ./docs")
                continue
            
            # Read file and convert to data URL
            with open(full_path, 'rb') as f:
                img_bytes = f.read()
            
            # Detect MIME type
            mime_type = mimetypes.guess_type(str(full_path))[0]
            if not mime_type or not mime_type.startswith("image/"):
                mime_type = "image/png"  # Fallback
            
            # Encode to base64
            b64 = base64.b64encode(img_bytes).decode('ascii')
            data_url = f"data:{mime_type};base64,{b64}"
            data_urls.append(data_url)
            
            logger.info(f"Loaded {fp} ({len(img_bytes)} bytes, {mime_type})")
            
        except Exception as e:
            logger.error(f"Failed to load {fp}: {e}")
            errors.append(f"{fp}: {str(e)}")
    
    if errors and not data_urls:
        return [], "; ".join(errors)
    
    if errors:
        logger.warning(f"Loaded {len(data_urls)}/{len(file_paths)} images (errors: {len(errors)})")
    
    return data_urls, None


def normalize_image_inputs(images: Optional[List[str]]) -> Tuple[List[str], Optional[str]]:
    """
    Normalize image inputs to data URLs.
    
    Args:
        images: List of image sources (http(s), data URL, or raw base64)
    
    Returns:
        (normalized_list, error_message)
    
    Accepts:
        - data:image/...;base64,... (kept as-is)
        - http(s)://... (downloaded and converted to data URL)
        - Raw base64 string (wrapped in data URL)
    """
    if not images:
        return [], "images list is empty"
    
    if not isinstance(images, list):
        return [], "images must be a list"
    
    if len(images) < 1 or len(images) > 3:
        return [], "images must contain 1 to 3 items"
    
    normalized: List[str] = []
    
    logger.info(f"Normalizing {len(images)} image input(s)")
    
    for im in images:
        if not isinstance(im, str):
            continue
        
        s = im.strip()
        if not s:
            continue
        
        # Already a data URL → keep as-is
        if s.startswith("data:"):
            normalized.append(s)
            logger.info("Image source: data URL (kept as-is)")
            continue
        
        # HTTP(S) URL → download and convert
        if s.startswith("http://") or s.startswith("https://"):
            logger.info(f"Downloading http(s) image: {s[:60]}...")
            du = download_to_data_url(s)
            if du:
                normalized.append(du)
                logger.info("Download successful, converted to data URL")
            else:
                logger.warning(f"Download failed, keeping http(s) URL as-is: {s[:60]}...")
                # Fallback: keep http(s) if download fails
                normalized.append(s)
            continue
        
        # Try raw base64
        try:
            base64.b64decode(s, validate=True)
            normalized.append(f"data:image/png;base64,{s}")
            logger.info("Raw base64 detected, wrapped in data URL")
        except Exception:
            # If not valid base64, keep as-is (best effort)
            logger.warning(f"Invalid base64, keeping as-is: {s[:60]}...")
            normalized.append(s)
    
    if not normalized:
        logger.error("No valid images after normalization")
        return [], "Could not prepare images (must be http(s), data:URL, or valid base64)"
    
    logger.info(f"Normalized {len(normalized)} image(s) successfully")
    return normalized, None


def coerce_to_list(val) -> Optional[List[str]]:
    """
    Coerce various UI inputs into a list of strings.
    - Already a list → clean and return
    - Single string → wrap as single-item list
    - None/empty → None
    """
    if val is None:
        return None
    
    if isinstance(val, list):
        out = [str(x).strip() for x in val if isinstance(x, (str, int, float)) and str(x).strip()]
        return out if out else None
    
    if isinstance(val, str):
        s = val.strip()
        return [s] if s else None
    
    # Fallback: wrap non-string scalars
    return [str(val).strip()]
