from ..base import AbstractHandler, HandlerError
from typing import Any, Dict, List, Optional

class JsonOpsHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "json_ops"

    def run(self, op: str = None, data: Any = None, path: str = None, default: Any = None,
            pick: Optional[List[str]] = None, rename: Optional[Dict[str,str]] = None,
            set_values: Optional[Dict[str, Any]] = None, remove: Optional[List[str]] = None,
            merge: Optional[Dict[str, Any]] = None, **kwargs) -> Dict:
        try:
            op = (op or "").lower()
            if op == "get":
                return {"result": self._get_path(data, path, default)}
            elif op == "set":
                src = data if isinstance(data, dict) else {}
                out = dict(src)
                for k, v in (set_values or {}).items():
                    out = self._set_path(out, k, v)
                return out
            elif op == "merge":
                src = data if isinstance(data, dict) else {}
                other = merge if isinstance(merge, dict) else {}
                out = dict(src)
                out.update(other)
                return out
            elif op == "pick":
                src = data if isinstance(data, dict) else {}
                keys = pick or []
                return {k: src.get(k) for k in keys}
            elif op == "rename":
                src = data if isinstance(data, dict) else {}
                out = dict(src)
                for k_old, k_new in (rename or {}).items():
                    if k_old in out:
                        out[k_new] = out.pop(k_old)
                return out
            elif op == "remove":
                src = data if isinstance(data, dict) else {}
                out = dict(src)
                for k in (remove or []):
                    out = self._del_path(out, k)
                return out
            else:
                raise HandlerError("json_ops: invalid op", "INVALID_OP", "validation", False)
        except HandlerError:
            raise
        except Exception as e:
            raise HandlerError(f"json_ops failed: {str(e)[:180]}", "JSON_OP_ERROR", "validation", False)

    def _get_path(self, obj: Any, dotted: Optional[str], default: Any) -> Any:
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
                    return default
            else:
                return default
            if cur is None:
                return default
        return cur

    def _set_path(self, obj: Dict, dotted: str, value: Any) -> Dict:
        parts = dotted.split('.')
        cur = obj
        for p in parts[:-1]:
            if p not in cur or not isinstance(cur[p], dict):
                cur[p] = {}
            cur = cur[p]
        cur[parts[-1]] = value
        return obj

    def _del_path(self, obj: Dict, dotted: str) -> Dict:
        parts = dotted.split('.')
        cur = obj
        for p in parts[:-1]:
            if p not in cur or not isinstance(cur[p], dict):
                return obj
            cur = cur[p]
        try:
            cur.pop(parts[-1], None)
        except Exception:
            pass
        return obj
