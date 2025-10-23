"""
Post filters and sorting for list_entities
"""
import re
from typing import List, Optional


def apply_post_filters(entities: List[dict], params: dict) -> List[dict]:
    flt = params.get('filters') or {}
    # tags_any
    tags_any = flt.get('tags_any') or []
    if isinstance(tags_any, list) and tags_any:
        tset = set(tags_any)
        entities = [e for e in entities if isinstance(e.get('tags'), list) and (set(e['tags']) & tset)]
    # name filter (exact on custom_name if present)
    name = flt.get('name')
    if isinstance(name, str) and name:
        entities = [e for e in entities if (e.get('custom_name') == name)]
    # custom_name_pattern (regex)
    pat = flt.get('custom_name_pattern')
    if isinstance(pat, str) and pat:
        try:
            rx = re.compile(pat)
            entities = [e for e in entities if isinstance(e.get('custom_name'), str) and rx.search(e['custom_name'])]
        except Exception:
            pass
    # types: if multiple provided, post-filter
    types = flt.get('types') or []
    if isinstance(types, list) and len(types) > 1:
        tset2 = set(types)
        entities = [e for e in entities if e.get('type') in tset2]
    return entities


def post_sort(entities: List[dict], sort_by: str, descending: bool, center: Optional[dict]) -> List[dict]:
    if sort_by == 'distance' and center is not None:
        def d(e):
            p = e.get('pos') or {'x': 0, 'y': 0, 'z': 0}
            dx = (p['x'] - center['x'])
            dy = (p['y'] - center['y'])
            dz = (p['z'] - center['z'])
            return dx*dx + dy*dy + dz*dz
        return sorted(entities, key=d, reverse=descending)
    if sort_by == 'y':
        return sorted(entities, key=lambda e: (e.get('pos', {}).get('y', 0)), reverse=descending)
    if sort_by == 'type':
        return sorted(entities, key=lambda e: (e.get('type') or ''), reverse=descending)
    if sort_by == 'name':
        return sorted(entities, key=lambda e: (e.get('custom_name') or ''), reverse=descending)
    return entities

__all__ = ['apply_post_filters', 'post_sort']
