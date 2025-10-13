import base64, json
from typing import Any, Dict, List, Tuple


def _encode_cursor(data: Dict[str, Any]) -> str:
    raw = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")


def _decode_cursor(cursor: str | None) -> Dict[str, Any]:
    if not cursor:
        return {"offset": 0}
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
        d = json.loads(raw)
        if not isinstance(d, dict) or "offset" not in d:
            return {"offset": 0}
        return d
    except Exception:
        return {"offset": 0}


def paginate_list(items: List[Any], limit: int, cursor: str | None) -> Tuple[List[Any], int, str | None]:
    state = _decode_cursor(cursor)
    offset = int(state.get("offset", 0))
    total = len(items)
    end = min(offset + limit, total)
    page = items[offset:end]
    next_c = _encode_cursor({"offset": end}) if end < total else None
    return page, total, next_c
