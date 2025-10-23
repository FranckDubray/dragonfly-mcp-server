
"""
Field decoders and counted fallback extraction for list_entities
"""
import re
import json
from typing import List, Optional
from .parse import _EYEH_RE

# Regex for array and UUID
_ARRAY_PAT = re.compile(r"\[(.*)\]")
_UUIDI_PAT = re.compile(r"\[I;\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*\]", re.IGNORECASE)


def _rhs_value(line: str) -> str:
    i = line.rfind(':')
    return line[i+1:].strip() if i != -1 else line.strip()


def _to_float(tok: str) -> Optional[float]:
    t = (tok or '').strip().rstrip(',')
    if not t:
        return None
    if t[-1:] in ('d','D','f','F'):
        t = t[:-1]
    try:
        return float(t)
    except Exception:
        return None


def decode_pos_line(line: str):
    val = _rhs_value(line)
    m = _ARRAY_PAT.search(val)
    if not m:
        return None
    inside = m.group(1)
    parts = [p.strip() for p in inside.split(',')]
    if len(parts) >= 3:
        x = _to_float(parts[0]); y = _to_float(parts[1]); z = _to_float(parts[2])
        if x is not None and y is not None and z is not None:
            return {'x': x, 'y': y, 'z': z}
    return None


def decode_rotation_line(line: str):
    val = _rhs_value(line)
    m = _ARRAY_PAT.search(val)
    if not m:
        return None, None
    inside = m.group(1)
    parts = [p.strip() for p in inside.split(',')]
    yaw = _to_float(parts[0]) if len(parts) > 0 else None
    pitch = _to_float(parts[1]) if len(parts) > 1 else None
    return yaw, pitch


def decode_tags_line(line: str):
    val = _rhs_value(line)
    m = _ARRAY_PAT.search(val)
    if not m:
        return None
    inside = m.group(1).strip()
    if not inside:
        return []
    out: List[str] = []
    for tok in [t.strip() for t in inside.split(',')]:
        if tok.startswith('"') and tok.endswith('"'):
            tok = tok[1:-1]
        elif tok.startswith("'") and tok.endswith("'"):
            tok = tok[1:-1]
        if tok:
            out.append(tok)
    return out


def decode_id_line(line: str):
    val = _rhs_value(line)
    if val.startswith('"') and val.endswith('"'):
        val = val[1:-1]
    return (val.split(':', 1)[-1]) if val else None


def decode_dimension_line(line: str):
    return decode_id_line(line)


def decode_uuid_line(line: str):
    val = _rhs_value(line)
    m = _UUIDI_PAT.search(val)
    if not m:
        return None
    return f"I;{m.group(1)},{m.group(2)},{m.group(3)},{m.group(4)}"


def decode_custom_name_line(line: str):
    val = _rhs_value(line)
    try:
        obj = json.loads(val)
        if isinstance(obj, dict):
            parts: List[str] = []
            if 'text' in obj and isinstance(obj['text'], str):
                parts.append(obj['text'])
            if 'extra' in obj and isinstance(obj['extra'], list):
                for e in obj['extra']:
                    if isinstance(e, dict) and isinstance(e.get('text'), str):
                        parts.append(e['text'])
            return ''.join(parts) if parts else None
        if isinstance(obj, str):
            return obj
    except Exception:
        pass
    if val.startswith('"') and val.endswith('"'):
        val = val[1:-1]
    return val.replace('\"', '"') if val else None


def _smart_split_lines(raw: str) -> List[str]:
    """Split raw server output into logical lines.
    Prefer newlines; if absent but multiple entries exist, split on the standard
    Paper/Bukkit phrase: "<name> has the following entity data:".
    """
    raw = raw or ''
    # First, normal newline-based split
    lines = [ln.strip() for ln in re.split(r"[\r\n]+", raw) if ln.strip()]
    if len(lines) > 1:
        return lines
    # Heuristic split when concatenated without newlines
    key_re = re.compile(r"([\"'])([^\"']*)\1\s+has the following entity data:\s*", re.IGNORECASE)
    spans = [m.start() for m in key_re.finditer(raw)]
    if len(spans) <= 1:
        return [raw.strip()] if raw.strip() else []
    spans.append(len(raw))
    segs: List[str] = []
    for a, b in zip(spans, spans[1:]):
        seg = raw[a:b].strip()
        if seg:
            segs.append(seg)
    return segs


def _get_lines_for_path(rcon, selector: str, path: str) -> List[str]:
    raw = rcon.execute(f"execute as {selector} run data get entity @s {path}")
    return _smart_split_lines(raw)


def fallback_fill_fields_counted(rcon, selector: str, fields: List[str], pos_ref: str) -> List[dict]:
    # Determine baseline count via 'id' then fallback to 'Pos'
    base_lines = _get_lines_for_path(rcon, selector, 'id')
    if not base_lines:
        base_lines = _get_lines_for_path(rcon, selector, 'Pos')
    n = len(base_lines)
    if n <= 0:
        return []
    entities_list: List[dict] = [
        {'uuid': None, 'custom_name': None, 'type': None, 'pos': None, 'yaw': None, 'pitch': None, 'tags': None, 'dimension': None}
        for _ in range(n)
    ]
    # Map requested fields to decoders
    field_map = {
        'pos': ('Pos', decode_pos_line),
        'yaw': ('Rotation', lambda s: decode_rotation_line(s)[0]),
        'pitch': ('Rotation', lambda s: decode_rotation_line(s)[1]),
        'tags': ('Tags', decode_tags_line),
        'type': ('id', decode_id_line),
        'custom_name': ('CustomName', decode_custom_name_line),
        'dimension': ('Dimension', decode_dimension_line),
        'uuid': ('UUID', decode_uuid_line),
    }
    needed = [f for f in fields if f in field_map]
    # Fetch and set per path
    cache: dict[str, List[str]] = {}
    for f in needed:
        path, _ = field_map[f]
        if path in cache:
            continue
        cache[path] = _get_lines_for_path(rcon, selector, path)
    for f in needed:
        path, decoder = field_map[f]
        lines = cache.get(path) or []
        # If line count doesn't match baseline, try to salvage by pairing min(common)
        m = min(len(lines), n)
        for i in range(m):
            try:
                val = decoder(lines[i])
                if f in ('yaw','pitch'):
                    if f == 'yaw':
                        entities_list[i]['yaw'] = val
                    else:
                        entities_list[i]['pitch'] = val
                else:
                    entities_list[i][f] = val
            except Exception:
                pass
    # pos_ref eyes adjustment
    if pos_ref == 'eyes' and 'pos' in needed:
        pos_lines = cache.get('Pos') or []
        m = min(len(pos_lines), n)
        for i in range(m):
            if entities_list[i].get('pos'):
                eyem = _EYEH_RE.search(pos_lines[i])
                dh = float(eyem.group(1)) if eyem else (1.62 if (entities_list[i].get('type') == 'player') else 1.0)
                entities_list[i]['pos']['y'] = entities_list[i]['pos']['y'] + dh
    return entities_list

__all__ = ['fallback_fill_fields_counted']

 
