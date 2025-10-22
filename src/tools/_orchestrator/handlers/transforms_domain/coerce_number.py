

from ..base import AbstractHandler, HandlerError
import re
from typing import Any, Dict

class CoerceNumberHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "coerce_number"

    def run(self, value: Any = None, default: float = 0.0, allow_percent: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Coerce an arbitrary value to a float number.
        - If value is already int/float -> return as float
        - If string -> extract first numeric token (e.g., '7.5', '10', '9/10' -> 9, '7.5/10' -> 7.5)
        - If allow_percent and string contains '%' -> take numeric part divided by 100
        - On failure -> return default
        Returns: {"number": float}
        """
        try:
            if isinstance(value, (int, float)):
                return {"number": float(value)}
            if value is None:
                return {"number": float(default)}
            s = str(value).strip()
            if not s:
                return {"number": float(default)}
            # Extract first float-like token
            m = re.search(r"[-+]?\d*\.?\d+", s)
            if not m:
                return {"number": float(default)}
            num = float(m.group(0))
            if allow_percent and "%" in s:
                num = num / 100.0
            return {"number": num}
        except Exception:
            return {"number": float(default)}
