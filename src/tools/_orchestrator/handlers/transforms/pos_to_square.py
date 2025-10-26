from ..base import AbstractHandler, HandlerError
import math
from typing import Dict, Any, List, Optional

class PosToSquareHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "pos_to_square"

    def run(self, items=None, origin=None, axis="+x", case_size=1.0, epsilon=0.35, **kwargs) -> dict:
        try:
            arr = items if isinstance(items, list) else []
            ox, oy, oz = self._get_origin(origin)
            cs = float(case_size or 1.0)
            eps = float(epsilon or 0.35)
            axis = (axis or "+x").lower()

            file_letters = "abcdefgh"
            rank_digits = "12345678"

            enriched: List[Dict[str, Any]] = []
            snap_map: Dict[str, str] = {}
            invalid: List[Dict[str, Any]] = []

            for it in arr:
                if not isinstance(it, dict):
                    continue
                pk = it.get("piece_key")
                pos = it.get("pos") or {}
                x, z = self._f(self._g(pos, "x")), self._f(self._g(pos, "z"))
                if x is None or z is None or not pk:
                    enriched.append({**it, "square": None})
                    invalid.append({**it})
                    continue

                if axis == "+z":
                    file_idx = int(round((z - oz) / cs))
                    rank_idx = int(round((x - ox) / cs))
                    cx = ox + rank_idx * cs
                    cz = oz + file_idx * cs
                else:
                    file_idx = int(round((x - ox) / cs))
                    rank_idx = int(round((z - oz) / cs))
                    cx = ox + file_idx * cs
                    cz = oz + rank_idx * cs

                dist = math.hypot((x - cx), (z - cz))
                if dist > eps:
                    enriched.append({**it, "square": None})
                    invalid.append({**it})
                    continue

                if 0 <= file_idx < 8 and 0 <= rank_idx < 8:
                    sq = f"{file_letters[file_idx]}{rank_digits[rank_idx]}"
                else:
                    sq = None
                    invalid.append({**it})

                enriched.append({**it, "square": sq})
                if sq and isinstance(pk, str):
                    snap_map[pk] = sq

            return {"items": enriched, "map": snap_map, "invalid": invalid}
        except Exception as e:
            raise HandlerError(f"pos_to_square failed: {str(e)[:200]}", "POS_TO_SQUARE_ERROR", "validation", False)

    def _get_origin(self, o: Optional[Dict[str, Any]]):
        if not isinstance(o, dict):
            return 0.0, 0.0, 0.0
        return float(o.get("x", 0.0)), float(o.get("y", 0.0)), float(o.get("z", 0.0))

    def _f(self, v):
        try:
            return float(v)
        except Exception:
            return None

    def _g(self, obj, key):
        try:
            return obj.get(key) if isinstance(obj, dict) else None
        except Exception:
            return None
