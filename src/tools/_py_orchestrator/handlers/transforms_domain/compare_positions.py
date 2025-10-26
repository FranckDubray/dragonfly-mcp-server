from ..base import AbstractHandler, HandlerError
from typing import Any, Dict

class ComparePositionsHandler(AbstractHandler):
    """
    Compare two maps prev and curr (piece_key -> square) to detect a unique move.

    Inputs: prev: dict, curr: dict
    Outputs:
      - unique: bool
      - piece_key: str | None
      - from: str | None
      - to: str | None
      - changed_count: int
    """

    @property
    def kind(self) -> str:
        return "compare_positions"

    def run(self, prev: Any = None, curr: Any = None, **kwargs) -> Dict[str, Any]:
        try:
            p = prev if isinstance(prev, dict) else {}
            c = curr if isinstance(curr, dict) else {}
            changed = []
            keys = set(list(p.keys()) + list(c.keys()))
            for k in keys:
                if p.get(k) != c.get(k):
                    changed.append(k)
            unique = (len(changed) == 1)
            piece_key = changed[0] if unique else None
            from_sq = p.get(piece_key) if unique else None
            to_sq = c.get(piece_key) if unique else None
            return {
                "unique": unique,
                "piece_key": piece_key,
                "from": from_sq,
                "to": to_sq,
                "changed_count": len(changed),
            }
        except Exception as e:
            raise HandlerError(f"compare_positions failed: {str(e)[:200]}", "COMPARE_POSITIONS_ERROR", "validation", False)
