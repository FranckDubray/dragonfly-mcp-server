"""
Parsing helpers for list_entities (quote-aware SNBT extraction, multi-compound split)
"""
import re
import json
from typing import Any, Dict, List, Optional, Tuple

# UUID patterns
_UUIDI_RE = re.compile(r"UUID\s*:\s*\[I;\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+)\s*\]")
_UUIDMOST_RE = re.compile(r"UUIDMost\s*:\s*(-?\d+).*?UUIDLeast\s*:\s*(-?\d+)", re.IGNORECASE)

# EyeHeight (for pos_ref="eyes")
_EYEH_RE = re.compile(r"EyeHeight\s*:\s*([-\d.]+)[fF]?", re.IGNORECASE)

# ---------------- Quote-aware helpers ----------------

def _extract_top_compound(s: str) -> str:
    if not s:
        return s
    start = s.find('{')
    if start == -1:
        return s
    depth = 0
    in_str = False
    str_q: Optional[str] = None
    esc = False
    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == str_q:
                in_str = False
            continue
        else:
            if ch in ('"', "'"):
                in_str = True
                str_q = ch
                continue
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return s[start:i+1]
    return s[start:]


def _skip_ws(s: str, i: int) -> int:
    n = len(s)
    while i < n and s[i].isspace():
        i += 1
    return i


def _balanced_block(s: str, i: int, open_ch: str, close_ch: str) -> Tuple[Optional[str], int]:
    n = len(s)
    if i >= n or s[i] != open_ch:
        return None, i
    depth = 1
    j = i + 1
    in_str = False
    str_q: Optional[str] = None
    esc = False
    while j < n and depth > 0:
        ch = s[j]
        if in_str:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == str_q:
                in_str = False
        else:
            if ch in ('"', "'"):
                in_str = True
                str_q = ch
            elif ch == open_ch:
                depth += 1
            elif ch == close_ch:
                depth -= 1
        j += 1
    if depth == 0:
        return s[i:j], j
    return None, i


def _quoted_string(s: str, i: int) -> Tuple[Optional[str], int]:
    n = len(s)
    if i >= n or s[i] not in ('"', "'"):
        return None, i
    q = s[i]
    j = i + 1
    buf = []
    esc = False
    while j < n:
        ch = s[j]
        if esc:
            buf.append(ch)
            esc = False
        elif ch == '\\':
            esc = True
        elif ch == q:
            return ''.join(buf), j + 1
        else:
            buf.append(ch)
        j += 1
    return None, i

# --------------- Key-value finder (case-insensitive) ---------------

def _find_key_value(body: str, key: str) -> Optional[str]:
    lb = body.lower()
    lk = key.lower()
    m = re.search(rf"\b{re.escape(lk)}\s*:\s*", lb)
    if not m:
        return None
    # FIX: locate colon from key start (not near end), then parse value
    colon = body.find(':', m.start())
    if colon == -1:
        return None
    i = colon + 1
    i = _skip_ws(body, i)
    if i >= len(body):
        return None
    ch = body[i]
    if ch in ('[', '{'):
        v, j = _balanced_block(body, i, ch, ']' if ch == '[' else '}')
        return v
    if ch in ('"', "'"):
        v, j = _quoted_string(body, i)
        return v
    j = i
    n = len(body)
    while j < n and body[j] not in (',', '}', ']'):
        j += 1
    return body[i:j].strip()

# ---------------- Field parsing ----------------

def _to_float(tok: Optional[str]) -> Optional[float]:
    if tok is None:
        return None
    t = tok.strip()
    if not t:
        return None
    if t[-1] in ('d', 'D', 'f', 'F'):
        t = t[:-1]
    try:
        return float(t)
    except Exception:
        return None


def _parse_pos(body: str) -> Optional[Dict[str, float]]:
    raw = _find_key_value(body, 'Pos')
    if not raw:
        return None
    inside = raw
    if inside.startswith('[') and inside.endswith(']'):
        inside = inside[1:-1]
    parts = [p.strip() for p in inside.split(',')]
    if len(parts) >= 3:
        x = _to_float(parts[0])
        y = _to_float(parts[1])
        z = _to_float(parts[2])
        if x is not None and y is not None and z is not None:
            return {'x': x, 'y': y, 'z': z}
    return None


def _parse_rotation(body: str) -> Tuple[Optional[float], Optional[float]]:
    raw = _find_key_value(body, 'Rotation')
    if not raw:
        return None, None
    inside = raw
    if inside.startswith('[') and inside.endswith(']'):
        inside = inside[1:-1]
    parts = [p.strip() for p in inside.split(',')]
    if len(parts) >= 2:
        return _to_float(parts[0]), _to_float(parts[1])
    return None, None


def _parse_tags(body: str) -> Optional[List[str]]:
    raw = _find_key_value(body, 'Tags')
    if raw is None:
        return None
    inside = raw
    if inside.startswith('[') and inside.endswith(']'):
        inside = inside[1:-1]
    if not inside.strip():
        return []
    out: List[str] = []
    toks = [t.strip() for t in inside.split(',')]
    for tok in toks:
        if not tok:
            continue
        if tok.startswith('"') and tok.endswith('"'):
            tok = tok[1:-1]
        elif tok.startswith("'") and tok.endswith("'"):
            tok = tok[1:-1]
        out.append(tok)
    return out


def _parse_type(body: str) -> Optional[str]:
    raw = _find_key_value(body, 'id')
    if not raw:
        return None
    val = raw.strip()
    if val.startswith('"') and val.endswith('"'):
        val = val[1:-1]
    if ':' in val:
        return val.split(':', 1)[-1]
    return val or None


def _parse_dimension(body: str) -> Optional[str]:
    raw = _find_key_value(body, 'Dimension')
    if not raw:
        return None
    val = raw.strip()
    if val.startswith('"') and val.endswith('"'):
        val = val[1:-1]
    if ':' in val:
        return val.split(':', 1)[-1]
    return val or None


def _parse_custom_name(body: str) -> Optional[str]:
    raw = _find_key_value(body, 'CustomName')
    if raw is None:
        return None
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            parts: List[str] = []
            if 'text' in obj and isinstance(obj['text'], str):
                parts.append(obj['text'])
            if 'extra' in obj and isinstance(obj['extra'], list):
                for e in obj['extra']:
                    if isinstance(e, dict) and isinstance(e.get('text'), str):
                        parts.append(e['text'])
            s = ''.join(parts) if parts else None
            if s:
                return s
        if isinstance(obj, str):
            return obj
    except Exception:
        pass
    tmp = raw.strip()
    if tmp.startswith('"') and tmp.endswith('"'):
        tmp = tmp[1:-1]
    return tmp.replace('\\"', '"')

# ---------------- Multi-compound extraction ----------------

def split_compounds_with_display(s: str) -> List[Tuple[Optional[str], str]]:
    out: List[Tuple[Optional[str], str]] = []
    n = len(s)
    i = 0
    in_str = False
    str_q: Optional[str] = None
    esc = False
    while i < n:
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == str_q:
                in_str = False
            i += 1
            continue
        else:
            if ch in ('"', "'"):
                in_str = True
                str_q = ch
                i += 1
                continue
            if ch == '{':
                comp, j = _balanced_block(s, i, '{', '}')
                if comp is None:
                    break
                name = None
                back_from = max(0, i - 160)
                prefix = s[back_from:i]
                m = re.search(r"([\"'])([^\"']+)\1\s+has the following entity data\s*:\s*$", prefix, re.IGNORECASE)
                if m:
                    name = m.group(2)
                out.append((name, comp))
                i = j
                continue
            i += 1
    return out

# ---------------- Public API ----------------

def parse_entity_from_line(s: str) -> Optional[dict]:
    s = (s or '').strip()
    if not s:
        return None
    body = _extract_top_compound(s)

    ent: Dict[str, Any] = {
        'uuid': None,
        'custom_name': None,
        'type': None,
        'pos': None,
        'yaw': None,
        'pitch': None,
        'tags': None,
        'dimension': None,
        'nbt_min': None,
    }
    ent['pos'] = _parse_pos(body)
    ent['yaw'], ent['pitch'] = _parse_rotation(body)

    m = _UUIDI_RE.search(body)
    if m:
        ent['uuid'] = f"I;{m.group(1)},{m.group(2)},{m.group(3)},{m.group(4)}"
    else:
        m2 = _UUIDMOST_RE.search(body)
        if m2:
            ent['uuid'] = f"Most:{m2.group(1)};Least:{m2.group(2)}"

    ent['tags'] = _parse_tags(body)
    ent['type'] = _parse_type(body)
    ent['dimension'] = _parse_dimension(body)
    ent['custom_name'] = _parse_custom_name(body)

    ent['nbt_min'] = {'CustomName': ent['custom_name'], 'Tags': ent['tags']}
    return ent

__all__ = [
    'parse_entity_from_line',
    'split_compounds_with_display',
    '_EYEH_RE',
]
