"""
Flatten Passengers/Riding for list_entities
"""
from typing import List, Tuple, Optional, Dict, Any
from .parse import parse_entity_from_line, _EYEH_RE


def _find_balanced_block(s: str, start_idx: int, open_ch: str, close_ch: str) -> Tuple[Optional[str], int]:
    depth = 0
    i = start_idx
    while i < len(s) and s[i] != open_ch:
        i += 1
    if i >= len(s) or s[i] != open_ch:
        return None, start_idx
    depth = 1
    j = i + 1
    while j < len(s) and depth > 0:
        ch = s[j]
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
        j += 1
    if depth == 0:
        return s[i+1:j-1], j
    return None, start_idx


def _split_top_level_compounds(s: str) -> List[str]:
    parts: List[str] = []
    depth = 0
    last = 0
    for i, ch in enumerate(s):
        if ch == '{':
            if depth == 0:
                last = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                parts.append(s[last:i+1])
        elif ch == ',' and depth == 0:
            pass
    return parts


def _extract_passengers_compounds(s: str) -> List[str]:
    key = 'Passengers:'
    idx = s.find(key)
    if idx == -1:
        return []
    i = s.find('[', idx)
    if i == -1:
        return []
    inside, _ = _find_balanced_block(s, i, '[', ']')
    if inside is None:
        return []
    return _split_top_level_compounds(inside)


def _extract_riding_compound(s: str) -> Optional[str]:
    key = 'Riding:'
    idx = s.find(key)
    if idx == -1:
        return None
    i = s.find('{', idx)
    if i == -1:
        return None
    inside, _ = _find_balanced_block(s, i, '{', '}')
    if inside is None:
        return None
    return '{' + inside + '}'


def flatten_from_snbt(s: str, include_passengers: bool, include_riding: bool, pos_ref: str, seen: set) -> List[Tuple[dict, str]]:
    out: List[Tuple[dict, str]] = []
    e = parse_entity_from_line(s)
    if e is None:
        return out
    # Adjust pos_ref eyes
    if pos_ref == 'eyes' and e.get('pos'):
        eyem = _EYEH_RE.search(s)
        if eyem:
            dh = float(eyem.group(1))
        else:
            dh = 1.62 if e.get('type') == 'player' else 1.0
        e['pos']['y'] = e['pos']['y'] + dh
    uid = e.get('uuid') or (e.get('type'), tuple((e.get('pos') or {}).values()))
    if uid not in seen:
        seen.add(uid)
        out.append((e, s))

    if include_passengers:
        try:
            childs = _extract_passengers_compounds(s)
            for cs in childs:
                out.extend(flatten_from_snbt(cs, True, include_riding, pos_ref, seen))
        except Exception:
            pass

    if include_riding:
        try:
            rs = _extract_riding_compound(s)
            if rs:
                out.extend(flatten_from_snbt(rs, include_passengers, True, pos_ref, seen))
        except Exception:
            pass

    return out

__all__ = ['flatten_from_snbt']
