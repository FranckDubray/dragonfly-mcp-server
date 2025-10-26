# Transform: date_ops — parametric date operations (format/add/diff)
# JSON in → JSON out, no I/O. <7KB

from datetime import datetime, timedelta, timezone
from ..base import AbstractHandler, HandlerError
from typing import Any, Dict, List, Optional

class DateOpsHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "date_ops"

    def run(self, ops: Optional[List[Dict]] = None, **kwargs) -> Dict:
        """
        ops: list of operations
          - {op:"format", value:any, to:"iso"|pattern|"YYYY-MM-DD", save_as:"key"}
          - {op:"add", value:any, days|hours|minutes|seconds:int, to?:pattern, save_as:"key"}
          - {op:"diff", a:any, b:any, unit:"days|hours|minutes|seconds", save_as:"key"}
        Accepts value/a/b as ISO string, epoch number, or dict {"result": str}.
        """
        out: Dict[str, Any] = {}
        for spec in ops or []:
            op = (spec.get("op") or "").lower()
            try:
                if op == "format":
                    val = self._coerce_dt(spec.get("value"))
                    if val is None:
                        out[spec.get("save_as", "result")] = None
                    else:
                        out[spec.get("save_as", "result")] = self._format_dt(val, spec.get("to", "iso"))
                elif op == "add":
                    val = self._coerce_dt(spec.get("value"))
                    if val is None:
                        out[spec.get("save_as", "result")] = None
                    else:
                        delta = timedelta(
                            days=float(spec.get("days", 0) or 0),
                            hours=float(spec.get("hours", 0) or 0),
                            minutes=float(spec.get("minutes", 0) or 0),
                            seconds=float(spec.get("seconds", 0) or 0),
                        )
                        res = val + delta
                        out[spec.get("save_as", "result")] = self._format_dt(res, spec.get("to", "iso"))
                elif op == "diff":
                    a = self._coerce_dt(spec.get("a"))
                    b = self._coerce_dt(spec.get("b"))
                    unit = (spec.get("unit") or "days").lower()
                    if a is None or b is None:
                        out[spec.get("save_as", "result")] = None
                    else:
                        delta = (a - b).total_seconds()
                        if unit == "seconds": v = delta
                        elif unit == "minutes": v = delta / 60.0
                        elif unit == "hours": v = delta / 3600.0
                        else: v = delta / 86400.0
                        out[spec.get("save_as", "result")] = v
                else:
                    raise HandlerError(
                        message=f"date_ops: unknown op '{op}'",
                        code="INVALID_OP",
                        category="validation",
                        retryable=False,
                    )
            except HandlerError:
                raise
            except Exception as e:
                raise HandlerError(
                    message=f"date_ops '{op}' failed: {str(e)[:180]}",
                    code="DATE_OP_ERROR",
                    category="validation",
                    retryable=False,
                )
        return out

    def _coerce_dt(self, value: Any) -> Optional[datetime]:
        if value is None:
            return None
        # Dict {result: ...}
        if isinstance(value, dict) and "result" in value:
            value = value.get("result")
        # Epoch seconds
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(float(value), tz=timezone.utc)
            except Exception:
                return None
        # String
        s = str(value).strip()
        if not s:
            return None
        try:
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None

    def _format_dt(self, dt: datetime, to: str) -> str:
        if not isinstance(dt, datetime):
            return ""
        if to == "iso":
            # Standardize to 'YYYY-MM-DDTHH:MM:SS+00:00'
            return dt.astimezone(timezone.utc).isoformat()
        if to == "YYYY-MM-DD":
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")
        # Assume strftime pattern
        try:
            return dt.astimezone(timezone.utc).strftime(to)
        except Exception:
            return dt.astimezone(timezone.utc).isoformat()
