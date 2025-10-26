from ..base import AbstractHandler, HandlerError
from typing import Any, Dict

class UciParseHandler(AbstractHandler):
    """
    Parse a UCI move string into components.
    Inputs:
      - uci: e.g., "e2e4", "e7e8q"
    Outputs:
      - from_sq: e.g., "e2"
      - to_sq: e.g., "e4"
      - promo: lowercase piece letter or None
    """
    @property
    def kind(self) -> str:
        return "uci_parse"

    def run(self, uci: Any = None, **kwargs) -> Dict[str, Any]:
        try:
            s = str(uci or "").strip()
            if len(s) < 4:
                raise HandlerError("uci_parse: invalid UCI", "INVALID_UCI", "validation", False)
            from_sq = s[0:2]
            to_sq = s[2:4]
            promo = s[4].lower() if len(s) >= 5 else None
            return {"from": from_sq, "to": to_sq, "promo": promo}
        except HandlerError:
            raise
        except Exception as e:
            raise HandlerError(f"uci_parse failed: {str(e)[:180]}", "UCI_PARSE_ERROR", "validation", False)

# TRANSFORM_META_START
{
  "io_type": "string->object",
  "description": "Parse a UCI move string into components",
  "inputs": [
    "- uci: string (e.g., 'e2e4', 'e7e8q')"
  ],
  "outputs": [
    "- from: string",
    "- to: string",
    "- promo: string|null"
  ]
}
# TRANSFORM_META_END
