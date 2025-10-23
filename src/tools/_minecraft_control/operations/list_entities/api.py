"""
API for list_entities (split: api + parse + filters_sort + selector + fallback)
"""
import logging
import time
from typing import List

from .selector import build_selector
from .parse import parse_entity_from_line, _EYEH_RE, split_compounds_with_display
from .filters_sort import apply_post_filters, post_sort
from .fallback import split_lines, fallback_fetch_entities

logger = logging.getLogger(__name__)


def _snbt_looks_truncated(raw: str) -> bool:
    if not raw:
        return True
    # Quick heuristics: missing closing braces
    opens = raw.count('{')
    closes = raw.count('}')
    if closes < opens:
        return True
    return False


def _normalize_name(name: str) -> str:
    if not isinstance(name, str):
        return name
    s = name.strip()
    # Strip repeated outer quotes, including patterns like '"foo"'
    for _ in range(3):
        if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
            s = s[1:-1].strip()
        else:
            break
    return s


def list_entities_op(params: dict, rcon, context: dict) -> dict:
    try:
        start = time.time()

        selector, center = build_selector(params, context)
        sort_by = (params.get('sort_by') or '').lower()
        descending = bool(params.get('descending', False))
        limit = int(params.get('limit') or 64)
        pos_ref = (params.get('pos_ref') or 'feet').lower()

        # Ensure command feedback is enabled so RCON receives output
        try:
            rcon.execute('gamerule sendCommandFeedback true')
        except Exception:
            pass

        # Retrieve full dump once (full raw string saved as-is)
        cmd = f"execute as {selector} run data get entity @s"
        raw = rcon.execute(cmd) or ''

        warnings: List[str] = []
        entities_list: List[dict] = []

        parts = split_compounds_with_display(raw)
        use_fallback = _snbt_looks_truncated(raw) or not parts
        if not use_fallback:
            # SNBT path
            for (disp_name, comp) in parts:
                e = parse_entity_from_line(comp)
                if e:
                    if pos_ref == 'eyes' and e.get('pos'):
                        eyem = _EYEH_RE.search(comp)
                        if eyem:
                            dh = float(eyem.group(1))
                        else:
                            dh = 1.62 if e.get('type') == 'player' else 1.0
                        e['pos']['y'] = e['pos']['y'] + dh
                    # Prefer display name if CustomName missing
                    if (not e.get('custom_name')) and disp_name:
                        e['custom_name'] = disp_name
                    entities_list.append(e)
        if use_fallback:
            # Fallback per-field fetch
            req_fields = params.get('fields')
            if isinstance(req_fields, list) and req_fields:
                requested_fields = [str(f) for f in req_fields]
            else:
                # Default comprehensive set
                requested_fields = ['uuid', 'name', 'custom_name', 'type', 'pos', 'yaw', 'pitch', 'tags', 'dimension']
            entities_list = fallback_fetch_entities(rcon, selector, pos_ref, requested_fields)
            if not raw.strip():
                warnings.append('No output received from server for full SNBT. Used fallback per-field queries.')
            else:
                warnings.append('Full SNBT parse unavailable or empty; used fallback per-field queries.')

        # Normalize custom_name aggressively (strip outer quotes)
        for e in entities_list:
            if 'custom_name' in e and e['custom_name'] is not None:
                e['custom_name'] = _normalize_name(e['custom_name'])

        # Filters and sort
        entities_list = apply_post_filters(entities_list, params)
        entities_list = post_sort(entities_list, sort_by, descending, center)

        # Limit
        truncated = False
        if limit and len(entities_list) > limit:
            entities_list = entities_list[:limit]
            truncated = True

        # Fields selection
        fields = params.get('fields')
        if isinstance(fields, list) and fields:
            key_map = {
                'uuid': 'uuid', 'name': 'name', 'custom_name': 'custom_name', 'type': 'type',
                'pos': 'pos', 'yaw': 'yaw', 'pitch': 'pitch', 'tags': 'tags', 'dimension': 'dimension',
                'nbt_min': 'nbt_min',
            }
            filtered_entities = []
            for e in entities_list:
                fe = {}
                for f in fields:
                    k = key_map.get(str(f))
                    if k is not None:
                        fe[k] = e.get(k)
                filtered_entities.append(fe)
            entities_out = filtered_entities
        else:
            entities_out = [
                {
                    'uuid': e.get('uuid'), 'name': e.get('name'), 'custom_name': e.get('custom_name'),
                    'type': e.get('type'), 'pos': e.get('pos'), 'yaw': e.get('yaw'), 'pitch': e.get('pitch'),
                    'tags': e.get('tags'), 'dimension': e.get('dimension'),
                }
                for e in entities_list
            ]

        elapsed = (time.time() - start) * 1000.0
        return {
            'success': True,
            'count': len(entities_out),
            'truncated': truncated,
            'center': center,
            'entities': entities_out,
            'time_ms': elapsed,
            'warnings': warnings,
            'selector_used': selector,
            'raw': raw,  # Full raw string returned
        }

    except Exception as e:
        logger.error(f"list_entities failed: {e}", exc_info=True)
        return {'success': False, 'error': str(e), 'error_type': type(e).__name__}

 
