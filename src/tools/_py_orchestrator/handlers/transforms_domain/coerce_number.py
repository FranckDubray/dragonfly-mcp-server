
# TRANSFORM_META_START
{
  "io_type": "any->number",
  "description": "Coerce an arbitrary value to a float number (with % support)",
  "inputs": [
    "- value: any",
    "- default: number (optional)",
    "- allow_percent: boolean (optional)"
  ],
  "outputs": [
    "- number: float"
  ]
}
# TRANSFORM_META_END

from ..base import AbstractHandler, HandlerError
import re
from typing import Any, Optional

class CoerceNumberHandler(AbstractHandler):
    """
    Convert various inputs to a float.
    - If value is int/float -> float(value)
    - If string -> extract first numeric token (supports "," decimal),
      optionally strips a trailing % when allow_percent=True.
    - Else -> default (or 0.0)

    Note: When allow_percent=True and input is like "85%", returns 85.0 (not 0.85).
    """

    @property
    def kind(self) -> str:
        return "coerce_number"

    def run(self, value: Any = None, default: Optional[float] = None, allow_percent: bool = False, **kwargs) -> dict:
        try:
            if isinstance(value, (int, float)):
                return {"number": float(value)}

            s = str(value).strip()
            if not s:
                return {"number": float(default if default is not None else 0.0)}

            # Handle percent
            if allow_percent and s.endswith('%'):
                s = s[:-1].strip()

            # Replace comma decimal
            s = s.replace(',', '.')

            # Try direct float
            try:
                return {"number": float(s)}
            except Exception:
                pass

            # Fallback: extract first numeric token
            m = re.search(r"-?\d+(?:\.\d+)?", s)
            if m:
                try:
                    return {"number": float(m.group(0))}
                except Exception:
                    pass

            return {"number": float(default if default is not None else 0.0)}
        except Exception as e:
            raise HandlerError(
                message=f"coerce_number failed: {str(e)[:200]}",
                code="COERCE_NUMBER_ERROR",
                category="validation",
                retryable=False,
            )
