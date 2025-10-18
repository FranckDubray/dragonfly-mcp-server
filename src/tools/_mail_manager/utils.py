

import re, time
from typing import Dict, Any, Tuple, List
from .db import set_state_kv, get_state_kv, utcnow_str
from .prompt_templates import USER_TEMPLATE
from .services.imap_helpers import resolve_spam_folder

MAX_BODY_CHARS = 30000
MAX_SUBJECT_CHARS = 512
MAX_ADDR_CHARS = 256
MAX_DATE_CHARS = 64


def heartbeat(db_path: str) -> None:
    set_state_kv(db_path, '__global__', 'heartbeat', utcnow_str())


def is_canceled(db_path: str) -> bool:
    return (get_state_kv(db_path, '__global__', 'cancel') or 'false') == 'true'


def cooperative_sleep(db_path: str, total_seconds: int, tick: float = 0.5) -> None:
    """Sleep in small chunks and exit early if cancel is requested."""
    remaining = float(total_seconds)
    while remaining > 0:
        if is_canceled(db_path):
            break
        t = tick if remaining > tick else remaining
        time.sleep(t)
        remaining -= t


def get_spam_folder_cached(db_path: str, provider: str) -> str:
    skey = f"spam_folder:{provider}"
    cached = get_state_kv(db_path, '__global__', skey)
    if cached:
        return cached
    folder = resolve_spam_folder(provider) or 'Spam'
    set_state_kv(db_path, '__global__', skey, folder)
    return folder


def _strip_html(html: str) -> str:
    # Lightweight HTML -> text:
    # - remove <script>/<style> blocks entirely (content included)
    # - remove HTML comments
    # - remove <img ...> tags and data:image base64 blobs
    # - strip remaining tags
    # - unescape entities
    # - collapse whitespace
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\\1>", " ", html)
    s = re.sub(r"(?is)<!--.*?-->", " ", s)
    s = re.sub(r"(?is)<img[^>]*>", " ", s)
    s = re.sub(r"(?is)data:image/[^;]+;base64,[A-Za-z0-9+/=]+", " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    try:
        import html as _html
        s = _html.unescape(s)
    except Exception:
        pass
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _strip_css_noise(text: str) -> str:
    """Remove common CSS-like noise that may leak into plain text parts.
    Conservative removal: selectors with {...}, standalone property: value; lines.
    """
    # Remove selector blocks: .class { ... } or #id { ... } or tag { ... }
    text = re.sub(r"(?ims)([.#]?[A-Za-z][A-Za-z0-9_-]*\s*\{[^}]{0,2000}\})", " ", text)
    # Remove inline property declarations: e.g., color:#333; margin:20px;
    text = re.sub(r"(?ims)\b[a-z-]{2,}\s*:\s*[^;}{\n]{1,120};?", " ", text)
    return text


def _strip_js_noise(text: str) -> str:
    """Lightweight removal of obvious JS residues in plain text (console.log, function(){}, var x=)."""
    text = re.sub(r"(?ims)\bconsole\.log\([^)]*\);?", " ", text)
    text = re.sub(r"(?ims)\bfunction\s*\([^)]*\)\s*\{[^}]{0,500}\}", " ", text)
    text = re.sub(r"(?ims)\bvar\s+[A-Za-z_][A-Za-z0-9_]*\s*=\s*[^;\n]{1,120};", " ", text)
    return text


def _strip_data_urls(text: str) -> str:
    return re.sub(r"(?is)data:image/[^;]+;base64,[A-Za-z0-9+/=]+", " ", text)


def _coerce_from_addr(val: Any) -> str:
    # Accept string, dicts with email/address, or lists of those
    def one(v: Any) -> str:
        if not v:
            return ''
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            for k in ('address','email','addr','value','name'):
                if isinstance(v.get(k), str) and v.get(k):
                    return v.get(k)
            return str(v)
        return str(v)
    if isinstance(val, list):
        return ", ".join([one(x) for x in val if one(x)])
    return one(val)


def extract_headers(msg: Dict[str, Any]) -> Tuple[str, str, str]:
    """Return (from_addr, subject, date_hdr) robustly from msg.
    - Prefer top-level keys; fallback to headers dict; fallback to common variants.
    - Truncate to safe sizes to fit DB schema.
    """
    headers = msg.get('headers') or {}
    # Subject
    subject = msg.get('subject')
    if not subject:
        subject = headers.get('subject') or headers.get('Subject')
    if not isinstance(subject, str):
        try:
            subject = str(subject or '')
        except Exception:
            subject = ''
    subject = subject.strip()[:MAX_SUBJECT_CHARS]

    # From
    from_val = msg.get('from')
    if not from_val:
        from_val = headers.get('from') or headers.get('From')
    from_addr = _coerce_from_addr(from_val).strip()[:MAX_ADDR_CHARS]

    # Date
    date_val = msg.get('date') or headers.get('date') or headers.get('Date') or msg.get('internal_date') or headers.get('received')
    if not isinstance(date_val, str):
        try:
            date_val = str(date_val or '')
        except Exception:
            date_val = ''
    date_hdr = date_val.strip()[:MAX_DATE_CHARS]

    return from_addr, subject, date_hdr


def extract_body_raw(msg: Dict[str, Any]) -> Tuple[str, str]:
    """Return (raw_text, source) without truncation.
    source in {'text','html','other'}
    """
    body = (msg or {}).get('body')
    if isinstance(body, dict):
        if isinstance(body.get('text'), str) and body.get('text'):
            txt = body.get('text').strip()
            # Even if declared as text, strip obvious CSS/JS/data URLs noise
            txt = _strip_css_noise(_strip_js_noise(_strip_data_urls(txt)))
            return txt, 'text'
        if isinstance(body.get('html'), str) and body.get('html'):
            return _strip_html(body.get('html')), 'html'
        return '', 'other'
    if isinstance(body, str):
        s = body.strip()
        # Heuristic: if looks like HTML, strip it; else remove CSS/JS/data URLs noise
        if '<' in s and '>' in s:
            return _strip_html(s), 'html'
        s = _strip_css_noise(_strip_js_noise(_strip_data_urls(s)))
        return s, 'text'
    try:
        s = str(body or '').strip()
        s = _strip_css_noise(_strip_js_noise(_strip_data_urls(s)))
        return s, 'other'
    except Exception:
        return '', 'other'


def extract_body_text(msg: Dict[str, Any]) -> str:
    raw, _ = extract_body_raw(msg)
    if len(raw) > MAX_BODY_CHARS:
        return raw[:MAX_BODY_CHARS]
    return raw


def sanitize_body(text: str) -> Dict[str, Any]:
    if not text:
        return {"text": "", "truncated": False, "chars": 0}
    original_len = len(text)
    # Remove lingering CSS/JS/data URLs once more for safety
    norm = _strip_css_noise(_strip_js_noise(_strip_data_urls(text)))
    norm = re.sub(r"\s+", " ", norm).strip()
    truncated = original_len > MAX_BODY_CHARS
    norm = norm[:MAX_BODY_CHARS]
    return {"text": norm, "truncated": truncated, "chars": original_len}


def user_prompt(from_addr: str, subject: str, body: str) -> str:
    return USER_TEMPLATE.format(from_addr=from_addr or '', subject=subject or '', body=body or '')
