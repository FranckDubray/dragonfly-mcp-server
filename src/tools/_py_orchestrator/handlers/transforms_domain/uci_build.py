from ..base import AbstractHandler, HandlerError
from typing import Any, Dict

class UciBuildHandler(AbstractHandler):
    """
    Build UCI string from from/to squares, with simple pawn promotion (to rank 1/8 -> q).

    Inputs:
      - from / from_: str (avoid Python keyword)
      - to: str
      - piece_letter: str (optional, for promotion detection)

    Output:
      - uci: str
    """

    @property
    def kind(self) -> str:
        return "uci_build"

    def run(self, _from: Any = None, from_: str = None, to: str = None, piece_letter: str = None, **kwargs) -> Dict[str, Any]:
        try:
            frm = from_ or _from or kwargs.get("from")
            to_sq = to
            if not frm or not to_sq:
                raise HandlerError("uci_build: missing from/to", "INVALID_INPUT", "validation", False)
            uci = f"{frm}{to_sq}"
            if (piece_letter or "").upper() == "P":
                rk = str(to_sq)[-1:] if isinstance(to_sq, str) else ""
                if rk in ("1", "8"):
                    uci += "q"
            return {"uci": uci}
        except HandlerError:
            raise
        except Exception as e:
            raise HandlerError(f"uci_build failed: {str(e)[:200]}", "UCI_BUILD_ERROR", "validation", False)

# TRANSFORM_META_START
{
  "io_type": "object->object",
  "description": "Build a UCI string from from/to squares, with pawn promotion handling",
  "inputs": [
    "- from|from_: string",
    "- to: string",
    "- piece_letter: string (optional — add 'q' when promoting a pawn to rank 1/8)"
  ],
  "outputs": [
    "- uci: string"
  ]
}
# TRANSFORM_META_END
