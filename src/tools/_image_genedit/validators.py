"""
Image input validation and normalization.
Converts all inputs (http(s), data URLs, raw base64) to data URLs for consistent processing.
"""
from typing import List, Optional
import base64

from .utils import download_to_data_url


def normalize_image_inputs(images: Optional[List[str]]) -> tuple[List[str], Optional[str]]:
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
    
    for im in images:
        if not isinstance(im, str):
            continue
        
        s = im.strip()
        if not s:
            continue
        
        # Already a data URL → keep as-is
        if s.startswith("data:"):
            normalized.append(s)
            continue
        
        # HTTP(S) URL → download and convert
        if s.startswith("http://") or s.startswith("https://"):
            du = download_to_data_url(s)
            if du:
                normalized.append(du)
            else:
                # Fallback: keep http(s) if download fails
                normalized.append(s)
            continue
        
        # Try raw base64
        try:
            base64.b64decode(s, validate=True)
            normalized.append(f"data:image/png;base64,{s}")
        except Exception:
            # If not valid base64, keep as-is (best effort)
            normalized.append(s)
    
    if not normalized:
        return [], "Could not prepare images (must be http(s), data:URL, or valid base64)"
    
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
