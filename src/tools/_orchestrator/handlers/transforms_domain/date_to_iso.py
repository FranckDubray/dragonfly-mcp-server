# Transform: date_to_iso - extract ISO date from possible JSON string

import json
from ..base import AbstractHandler, HandlerError

class DateToIsoHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "date_to_iso"

    def run(self, value=None, **kwargs):
        """
        Normalize any date-like value to a plain ISO8601 string.
        Accepts:
          - plain ISO string → returns as-is
          - dict with {"result": "ISO"} → returns ISO
          - JSON string like '{"result":"ISO"}' → parse and return ISO
        """
        if value is None:
            return {"result": None}
        
        # Dict with result
        if isinstance(value, dict) and isinstance(value.get("result"), str):
            return {"result": value["result"]}
        
        # String
        if isinstance(value, str):
            s = value.strip()
            # Looks like JSON dict with result
            if s.startswith("{") and '"result"' in s:
                try:
                    obj = json.loads(s)
                    if isinstance(obj, dict) and isinstance(obj.get("result"), str):
                        return {"result": obj["result"]}
                except Exception:
                    # fall through to raw string
                    pass
            # Otherwise assume already ISO string
            return {"result": s}
        
        # Fallback: stringify
        return {"result": str(value)}
