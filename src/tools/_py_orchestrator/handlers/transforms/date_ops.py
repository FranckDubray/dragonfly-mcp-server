# TRANSFORM_META_START
{
  "io_type": "json->json",
  "description": "Date utilities: produce ymd (YYYY-MM-DD) and RFC-like since string (DD-Mon-YYYY) from input datetime or 'today'",
  "inputs": [
    "- ops: list[object] (supported ops: {op:'from_datetime_to_ymd_rfc', datetime, input_format?} | {op:'today_ymd_rfc', tz?})"
  ],
  "outputs": [
    "- object: object (keys produced: ymd, since_rfc)"
  ]
}
# TRANSFORM_META_END

from ..base import AbstractHandler, HandlerError
from typing import Any, Dict, List
from datetime import datetime, timezone

_MON = {
    "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun",
    "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"
}

class DateOpsHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "date_ops"

    def run(self, ops: List[Dict[str, Any]] | None = None, **kwargs) -> Dict[str, Any]:
        try:
            ops = ops or []
            out: Dict[str, Any] = {}
            for op in ops:
                name = str((op or {}).get("op") or "").strip().lower()
                if name == "from_datetime_to_ymd_rfc":
                    dt = str((op or {}).get("datetime") or "").strip()
                    input_fmt = (op or {}).get("input_format")  # optional
                    ymd = self._to_ymd(dt, input_fmt)
                    out["ymd"] = ymd
                    out["since_rfc"] = self._to_rfc_from_ymd(ymd)
                elif name == "today_ymd_rfc":
                    # tz unused for now; we use UTC by default
                    now = datetime.now(timezone.utc)
                    ymd = now.strftime("%Y-%m-%d")
                    out["ymd"] = ymd
                    out["since_rfc"] = self._to_rfc_from_ymd(ymd)
                else:
                    raise HandlerError(f"date_ops: invalid op '{name}'", "INVALID_OP", "validation", False)
            return out
        except HandlerError:
            raise
        except Exception as e:
            raise HandlerError(f"date_ops failed: {str(e)[:200]}", "DATE_OPS_ERROR", "validation", False)

    def _to_ymd(self, dt: str, input_fmt: str | None) -> str:
        if not dt:
            return ""
        # Try input_fmt if provided, else try two common formats
        fmts = [input_fmt] if input_fmt else ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"]
        for fmt in [f for f in fmts if f]:
            try:
                d = datetime.strptime(dt, fmt)
                return d.strftime("%Y-%m-%d")
            except Exception:
                continue
        # Fallback: slice first 10 chars if looks like YYYY-MM-DD
        s = dt[:10]
        if len(s) == 10 and s[4] == '-' and s[7] == '-':
            return s
        return ""

    def _to_rfc_from_ymd(self, ymd: str) -> str:
        if len(ymd) >= 10 and ymd[4] == '-' and ymd[7] == '-':
            y = ymd[0:4]; m = ymd[5:7]; d = ymd[8:10]
            mm = _MON.get(m)
            if mm:
                return f"{d}-{mm}-{y}"
        return ymd or ""
