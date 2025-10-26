from datetime import datetime, timezone
from ..base import AbstractHandler

class FilterMultiByDateHandler(AbstractHandler):
    """
    Filter multiple sources by date >= cutoff_iso in a single pass.

    Inputs:
      - cutoff_iso: ISO8601 cutoff (e.g., '2025-10-15T22:36:34Z')
      - items_map: dict name->list[dict], e.g., {"news": [...], "reddit": [...]}  (optional)
      - date_paths: dict name->str date field path (dotted), e.g., {"news": "published_at"}
      - unix_seconds: dict name->bool (if True, interpret field as Unix epoch seconds)

    Outputs (flattened by name): for each name in items_map
      - f"{name}_items_recent": filtered list
      - f"{name}_kept": int
      - f"{name}_dropped": int
    """
    @property
    def kind(self) -> str:
        return "filter_multi_by_date"

    def run(self, cutoff_iso=None, items_map=None, date_paths=None, unix_seconds=None, **kwargs):
        res = {}
        if not cutoff_iso or not isinstance(items_map, dict) or not isinstance(date_paths, dict):
            # Nothing to do, return empty metrics for known keys if any
            for name, items in (items_map or {}).items():
                res[f"{name}_items_recent"] = []
                res[f"{name}_kept"] = 0
                res[f"{name}_dropped"] = len(items) if isinstance(items, list) else 0
            return res
        cutoff = self._parse_iso(cutoff_iso)
        if cutoff is None:
            for name, items in items_map.items():
                res[f"{name}_items_recent"] = []
                res[f"{name}_kept"] = 0
                res[f"{name}_dropped"] = len(items) if isinstance(items, list) else 0
            return res

        unix_map = unix_seconds if isinstance(unix_seconds, dict) else {}

        for name, items in items_map.items():
            path = date_paths.get(name)
            as_unix = bool(unix_map.get(name, False))
            if not isinstance(items, list) or not path:
                res[f"{name}_items_recent"] = []
                res[f"{name}_kept"] = 0
                res[f"{name}_dropped"] = len(items) if isinstance(items, list) else 0
                continue
            kept_items = []
            dropped = 0
            for it in items:
                try:
                    dt_val = self._get_path(it, path)
                    dt = self._parse_unix(dt_val) if as_unix else self._parse_iso(dt_val)
                    if dt is None:
                        dropped += 1
                        continue
                    if dt >= cutoff:
                        kept_items.append(it)
                    else:
                        dropped += 1
                except Exception:
                    dropped += 1
            res[f"{name}_items_recent"] = kept_items
            res[f"{name}_kept"] = len(kept_items)
            res[f"{name}_dropped"] = dropped
        return res

    def _get_path(self, obj, path):
        cur = obj
        for part in str(path).split('.'):
            if isinstance(cur, list):
                idx = int(part)
                cur = cur[idx]
            elif isinstance(cur, dict):
                cur = cur.get(part)
            else:
                return None
        return cur

    def _parse_iso(self, s):
        if not s:
            return None
        try:
            txt = str(s).strip()
            if txt.endswith('Z'):
                txt = txt[:-1] + "+00:00"
            dt = datetime.fromisoformat(txt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None

    def _parse_unix(self, val):
        try:
            sec = float(val)
            return datetime.fromtimestamp(sec, tz=timezone.utc)
        except Exception:
            return None

# TRANSFORM_META_START
{
  "io_type": "object->object",
  "description": "Filter multiple named lists by date cutoff in one pass (per-name metrics)",
  "inputs": [
    "- cutoff_iso: string (ISO8601, e.g. '2025-10-15T22:36:34Z')",
    "- items_map: object name->list[object]",
    "- date_paths: object name->string (dotted path to date field)",
    "- unix_seconds: object name->boolean (interpret field as epoch seconds)"
  ],
  "outputs": [
    "- {name}_items_recent: list[object]",
    "- {name}_kept: integer",
    "- {name}_dropped: integer"
  ]
}
# TRANSFORM_META_END
