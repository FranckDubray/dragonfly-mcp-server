"""
Selector building for list_entities
"""
from typing import Any, Dict, List, Optional, Tuple

def _round_int(v: Any, default: int = 0) -> int:
    try:
        return int(round(float(v)))
    except Exception:
        return default


def build_selector(params: dict, context: dict) -> Tuple[str, Optional[dict]]:
    """Return (selector_string, center_used_if_any).
    If params.selector is provided and not equal to '@e', it is returned as-is with center=None.
    Otherwise we synthesize an @e[...] with filters and area.
    """
    base_selector = (params.get('selector') or '@e').strip()

    if base_selector != '@e':
        return base_selector, None

    area = params.get('area') or {}
    mode = (area.get('mode') or 'sphere').lower()
    rel = params.get('relative_to_player', True)

    center = None
    if 'center' in area and isinstance(area['center'], dict):
        c = area['center']
        center = {
            'x': _round_int(c.get('x', 0), 0),
            'y': _round_int(c.get('y', 64), 64),
            'z': _round_int(c.get('z', 0), 0),
        }
    elif rel:
        base = context.get('resolved_position', {'x': 0, 'y': 64, 'z': 0})
        center = {'x': _round_int(base.get('x', 0), 0), 'y': _round_int(base.get('y', 64), 64), 'z': _round_int(base.get('z', 0), 0)}

    parts: List[str] = []

    # Types: selector supports only one type; for multiple, we will post-filter later
    types = params.get('filters', {}).get('types') if isinstance(params.get('filters'), dict) else None
    if isinstance(types, list) and len(types) == 1 and types[0]:
        parts.append(f"type={types[0]}")

    # Tags
    flt = params.get('filters') or {}
    tags_all = flt.get('tags_all') or []
    tags_none = flt.get('tags_none') or []
    if isinstance(tags_all, list):
        for t in tags_all:
            parts.append(f"tag={t}")
    if isinstance(tags_none, list):
        for t in tags_none:
            parts.append(f"tag=!{t}")

    # Area
    if mode == 'aabb':
        aabb = area.get('aabb') or {}
        amin = aabb.get('min') or {}
        amax = aabb.get('max') or {}
        min_x = _round_int(amin.get('x', (center or {}).get('x', 0)))
        min_y = _round_int(amin.get('y', (center or {}).get('y', 64)))
        min_z = _round_int(amin.get('z', (center or {}).get('z', 0)))
        max_x = _round_int(amax.get('x', min_x))
        max_y = _round_int(amax.get('y', min_y))
        max_z = _round_int(amax.get('z', min_z))
        dx = max(0, max_x - min_x)
        dy = max(0, max_y - min_y)
        dz = max(0, max_z - min_z)
        parts.append(f"x={min_x}")
        parts.append(f"y={min_y}")
        parts.append(f"z={min_z}")
        parts.append(f"dx={dx}")
        parts.append(f"dy={dy}")
        parts.append(f"dz={dz}")
    else:
        if center is not None:
            parts.append(f"x={center['x']}")
            parts.append(f"y={center['y']}")
            parts.append(f"z={center['z']}")
        radius = area.get('radius')
        try:
            r = float(radius) if radius is not None else 0.0
        except Exception:
            r = 0.0
        if r > 0:
            parts.append(f"distance=..{r}")

    # Sort & limit
    sort_by = (params.get('sort_by') or '').lower()
    limit = int(params.get('limit') or 64)
    if sort_by == 'distance' and center is not None:
        parts.append('sort=nearest')
    if limit and limit > 0:
        parts.append(f"limit={limit}")

    selector = '@e'
    if parts:
        selector += '[' + ','.join(parts) + ']'
    return selector, center
