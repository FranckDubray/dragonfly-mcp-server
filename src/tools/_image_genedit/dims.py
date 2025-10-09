from typing import Optional, Tuple, List
import base64

# Lightweight width/height extraction without external deps
# Supports PNG (IHDR) and JPEG (SOF markers). If parsing fails, returns None.


def _read_png_size(data: bytes) -> Tuple[Optional[int], Optional[int]]:
    # PNG signature (8 bytes) + IHDR chunk: length(4) 'IHDR'(4) width(4) height(4)
    if len(data) < 24:
        return None, None
    sig = data[:8]
    if sig != b"\x89PNG\r\n\x1a\n":
        return None, None
    # IHDR should be the first chunk
    if data[12:16] != b"IHDR":
        return None, None
    try:
        w = int.from_bytes(data[16:20], 'big')
        h = int.from_bytes(data[20:24], 'big')
        return w, h
    except Exception:
        return None, None


def _read_jpeg_size(data: bytes) -> Tuple[Optional[int], Optional[int]]:
    # Minimal SOI check
    if len(data) < 4 or data[0:2] != b"\xff\xd8":
        return None, None
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        i += 2
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            # SOF segment
            if i + 7 > len(data):
                return None, None
            length = int.from_bytes(data[i:i+2], 'big')
            if i + length > len(data):
                return None, None
            precision = data[i+2]
            h = int.from_bytes(data[i+3:i+5], 'big')
            w = int.from_bytes(data[i+5:i+7], 'big')
            return w, h
        else:
            if i + 2 > len(data):
                return None, None
            length = int.from_bytes(data[i:i+2], 'big')
            i += length
    return None, None


def _data_url_to_bytes(data_url: str) -> bytes:
    # Expect format: data:image/<ext>;base64,<payload>
    try:
        header, b64 = data_url.split(',', 1)
        return base64.b64decode(b64)
    except Exception:
        return b""


def infer_from_sources(images_data_urls: List[str]) -> Tuple[Optional[int], Optional[int]]:
    """Try to infer a common width/height from sources. Return (w,h) or (None,None)."""
    sizes = []
    for url in images_data_urls:
        data = _data_url_to_bytes(url)
        if not data:
            continue
        w, h = _read_png_size(data)
        if w is None or h is None:
            w, h = _read_jpeg_size(data)
        if w is not None and h is not None:
            sizes.append((w, h))
    if not sizes:
        return None, None
    # If single source → inherit
    if len(sizes) == 1:
        return sizes[0]
    # If all same → inherit
    first = sizes[0]
    if all(s == first for s in sizes[1:]):
        return first
    return None, None
