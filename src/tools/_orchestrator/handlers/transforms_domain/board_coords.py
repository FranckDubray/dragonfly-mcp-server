from ..base import AbstractHandler, HandlerError
from typing import Any, Dict, List, Optional

class BoardCoordsHandler(AbstractHandler):
    """
    Generate 8x8 board coordinates (centers and AABBs) from worker chess config.

    Inputs:
      - origin: {x,y,z}  (center of a1 when white_near_origin=True)
      - axis: "+x" or "+z" (files progress along this axis)
      - case_size: block size of one square (float)
      - y_level: integer Y level to paint/spawn
      - white_near_origin: bool (default True). If False, ranks are inverted (a8 near origin).

    Outputs:
      - squares: list[{
          "square": "a1".."h8",
          "file_idx": 0..7,
          "rank_idx": 0..7,
          "color": "light"|"dark",
          "center": {x,y,z},
          "aabb": {"min":{x,y,z}, "max":{x,y,z}}
        }]
    """

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
                    # If white is near origin: a1 at (0,0). If not, a8 near origin -> invert rank index.
                    r_index = ri if white_near_origin else (7 - ri)
                    f_index = fi  # files not inverted; a-file near origin along file axis

                    if axis == "+z":
                        cx = ox + (r_index * cs)
                        cz = oz + (f_index * cs)
                    else:  # "+x"
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
