# Transform: array_ops — parametric list operations (filter/unique_by/sort_by/map/take/skip)
# JSON in → JSON out, no I/O. <7KB

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from ..base import AbstractHandler, HandlerError

class ArrayOpsHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "array_ops"

    def run(self, op: str = None, items: Any = None, predicate: Dict = None,
            key: str = None, order: str = "asc", fields: Optional[List[str]] = None,
            count: int = 0, **kwargs) -> Dict:
        try:
            op = (op or "").lower()
            arr = items if isinstance(items, list) else []
            if op == "filter":
                pred = predicate or {}
                kept = []
                dropped = 0
                for it in arr:
                    if self._match(it, pred):
                        kept.append(it)
                    else:
                        dropped += 1
                return {"items": kept, "kept": len(kept), "dropped": dropped}
            elif op == "unique_by":
                seen = set()
                out = []
                for it in arr:
                    v = self._get_path(it, key)
                    if v in seen:
                        continue
                    seen.add(v)
                    out.append(it)
                return {"items": out, "kept": len(out)}
            elif op == "sort_by":
                rev = (order or "asc").lower() == "desc"
                try:
                    out = sorted(arr, key=lambda it: self._get_path(it, key), reverse=rev)
                except Exception:
                    out = list(arr)
                return {"items": out}
            elif op == "map":
                fields = fields or []
                mapped = []
                for it in arr:
                    if not isinstance(it, dict):
                        mapped.append(it)
                        continue
                    mapped.append({f: it.get(f) for f in fields})
                return {"items": mapped}
            elif op == "take":
                n = int(count or 0)
                return {"items": arr[:max(0, n)]}
            elif op == "skip":
                n = int(count or 0)
                return {"items": arr[max(0, n):]}
            else:
                raise HandlerError("array_ops: invalid op", "INVALID_OP", "validation", False)
        except HandlerError:
            raise
        except Exception as e:
            raise HandlerError(f"array_ops failed: {str(e)[:180]}", "ARRAY_OP_ERROR", "validation", False)

    def _get_path(self, obj: Any, dotted: Optional[str]) -> Any:
        if dotted is None:
            return obj
        cur = obj
        for part in str(dotted).split('.'):
            if isinstance(cur, dict):
                cur = cur.get(part)
            elif isinstance(cur, list):
                try:
                    cur = cur[int(part)]
                except Exception:
                    return None
            else:
                return None
        return cur

    def _match(self, it: Any, pred: Dict) -> bool:
        kind = (pred.get("kind") or "truthy").lower()
        path = pred.get("path")
        val = self._get_path(it, path) if path else it
        if kind == "truthy":
            return bool(val)
        if kind == "has_key":
            return isinstance(val, dict) and pred.get("key") in val
        if kind == "in_list":
            return val in (pred.get("list") or [])
        if kind == "compare":
            op = pred.get("operator", "==")
            right = pred.get("value")
            try:
                lv = float(val)
                rv = float(right)
            except Exception:
                lv, rv = str(val), str(right)
            if op == "==": return lv == rv
            if op == "!=": return lv != rv
            if op == ">":  return lv >  rv
            if op == ">=": return lv >= rv
            if op == "<":  return lv <  rv
            if op == "<=": return lv <= rv
            return False
        if kind == "date_gte":
            cutoff = pred.get("cutoff")
            unix = bool(pred.get("unix"))
            if cutoff is None: return True
            cdt = self._parse_iso(cutoff)
            if cdt is None: return True
            if val is None: return False
            if unix:
                try:
                    vdt = datetime.fromtimestamp(float(val), tz=timezone.utc)
                except Exception:
                    return False
            else:
                vdt = self._parse_iso(val)
                if vdt is None:
                    return False
            return vdt >= cdt
        if kind == "regex":
            import re
            pattern = pred.get("pattern")
            if pattern is None:
                return False
            try:
                return re.search(pattern, str(val) or "") is not None
            except re.error:
                return False
        return False

    def _parse_iso(self, s: Any):
        try:
            txt = str(s).strip()
            if txt.endswith("Z"):
                txt = txt[:-1] + "+00:00"
            dt = datetime.fromisoformat(txt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None
# TRANSFORM_META_START
{
  "io_type": "list->list",
  "description": "Parametric list operations (filter, map, sort_by, unique_by, take, skip)",
  "inputs": [
    "- op: string (filter|map|sort_by|unique_by|take|skip)",
    "- items: list[any]",
    "- predicate: object (when op=filter)",
    "- key: string (when op=sort_by|unique_by)",
    "- order: string (asc|desc) (when op=sort_by)",
    "- fields: list[string] (when op=map)",
    "- count: integer (when op=take|skip)"
  ],
  "outputs": [
    "- items: list[any]"
  ]
}
# TRANSFORM_META_END
