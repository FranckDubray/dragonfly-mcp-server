from datetime import datetime, timezone
from ..base import AbstractHandler

class FilterByDateHandler(AbstractHandler):
    """
    Filter items by date >= cutoff_iso.

    Inputs:
      - items: list[dict]
      - date_path: dotted path to date field (e.g., 'published_at', 'created_utc', 'publication_date')
      - cutoff_iso: ISO8601 cutoff (e.g., '2025-10-15T22:36:34Z')
      - unix_seconds: bool (if True, interpret field as Unix epoch seconds)
    Outputs:
      - items_recent: filtered list
      - kept: int
      - dropped: int
    """
    @property
    def kind(self) -> str:
        return "filter_by_date"

    def run(self, items=None, date_path="published_at", cutoff_iso=None, unix_seconds=False, **kwargs):
        if not isinstance(items, list):
            return {"items_recent": [], "kept": 0, "dropped": 0}
        if not cutoff_iso:
            # No cutoff provided -> return empty to be safe
            return {"items_recent": [], "kept": 0, "dropped": len(items)}
        cutoff = self._parse_iso(cutoff_iso)
        if cutoff is None:
            return {"items_recent": [], "kept": 0, "dropped": len(items)}

        kept_items = []
        dropped = 0
        for it in items:
            try:
                dt_val = self._get_path(it, date_path)
                dt = self._parse_unix(dt_val) if unix_seconds else self._parse_iso(dt_val)
                if dt is None:
                    dropped += 1
                    continue
                if dt >= cutoff:
                    kept_items.append(it)
                else:
                    dropped += 1
            except Exception:
                dropped += 1
        return {"items_recent": kept_items, "kept": len(kept_items), "dropped": dropped}

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
            # Handle trailing Z
            if txt.endswith('Z'):
                txt = txt[:-1] + "+00:00"
            # If no timezone, assume UTC
            if 'T' in txt and ('+' not in txt and '-' in txt[10:] is False):
                # crude check; but datetime.fromisoformat handles missing tz; we force UTC
                dt = datetime.fromisoformat(txt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
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
