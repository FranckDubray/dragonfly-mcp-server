from typing import List, Optional
import os
import re
import base64
import mimetypes
import requests

_IMG_URL_RE = re.compile(r"https?://[^\s\"'>]+\.(?:png|jpe?g|webp)(?:\?[^\s\"'>]*)?", re.IGNORECASE)
_IMG_TAG_RE = re.compile(r"<img[^>]+src=\"([^\"]+)\"", re.IGNORECASE)


def extract_image_urls(text: str) -> List[str]:
    urls: List[str] = []
    if not isinstance(text, str) or not text:
        return urls
    try:
        urls.extend(_IMG_URL_RE.findall(text))
        for m in _IMG_TAG_RE.findall(text):
            if isinstance(m, str) and m.startswith("http"):
                urls.append(m)
    except Exception:
        pass
    # dedupe preserving order
    seen = set()
    out: List[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _verify_ssl() -> bool:
    v = os.getenv("LLM_VERIFY_SSL", "").strip().lower()
    if v == "":
        return False
    return v not in ("0", "false", "no", "off")


def download_to_data_url(url: str, timeout: int = 30) -> Optional[str]:
    try:
        r = requests.get(url, stream=True, timeout=timeout, verify=_verify_ssl())
        r.raise_for_status()
        ctype = (r.headers.get("Content-Type") or mimetypes.guess_type(url)[0] or "image/png")
        if not ctype.startswith("image/"):
            ctype = "image/png"
        b64 = base64.b64encode(r.content).decode("ascii")
        return f"data:{ctype};base64,{b64}"
    except Exception:
        return None
