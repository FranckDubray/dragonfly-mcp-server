from ..base import AbstractHandler, HandlerError
from typing import Any, Dict, List, Optional

class BoardCoordsHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "board_coords"

    def run(self, origin: Optional[Dict[str, Any]] = None, axis: str = "+x", case_size: float = 1.0,
            y_level: float = 64.0, white_near_origin: bool = True, **kwargs) -> Dict[str, Any]:
        try:
            ox, oy, oz = self._origin(origin)
            cs = float(case_size or 1.0)
            y = float(y_level if y_level is not None else oy)
            axis = (axis or "+x").lower().strip()
            white_near_origin = bool(white_near_origin)
            half = cs / 2.0

            file_letters = "abcdefgh"
            rank_digits = "12345678"

            squares: List[Dict[str, Any]] = []
            for fi in range(8):
                for ri in range(8):
                    r_index = ri if white_near_origin else (7 - ri)
                    f_index = fi
                    if axis == "+z":
                        cx = ox + (r_index * cs)
                        cz = oz + (f_index * cs)
                    else:
                        cx = ox + (f_index * cs)
                        cz = oz + (r_index * cs)
                    square = f"{file_letters[fi]}{rank_digits[ri]}"
                    color = "light" if ((fi + ri) % 2 == 0) else "dark"
                    item = {
                        "square": square,
                        "file_idx": fi,
                        "rank_idx": ri,
                        "color": color,
                        "center": {"x": cx, "y": y, "z": cz},
                        "aabb": {
                            "min": {"x": cx - half, "y": y, "z": cz - half},
                            "max": {"x": cx + half, "y": y, "z": cz + half}
                        }
                    }
                    squares.append(item)
            return {"squares": squares}
        except Exception as e:
            raise HandlerError(f"board_coords failed: {str(e)[:200]}", "BOARD_COORDS_ERROR", "validation", False)

    def _origin(self, o: Optional[Dict[str, Any]]):
        try:
            return float(o.get("x", 0.0)), float(o.get("y", 0.0)), float(o.get("z", 0.0)) if isinstance(o, dict) else (0.0, 0.0, 0.0)
        except Exception:
            return 0.0, 0.0, 0.0
