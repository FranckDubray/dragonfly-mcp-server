from ..base import AbstractHandler, HandlerError
import re
from typing import Any, Dict, List, Optional

class NormalizeEntitiesHandler(AbstractHandler):
    """
    Normalize raw entities from Minecraft list_entities into a chess-friendly schema.

    Input:
      - items: list of entities, each like {custom_name, name?, pos:{x,y,z}, tags:[], uuid}
      - piece_tag_map: optional map from tag -> letter (e.g., pawn->P, knight->N ...)

    Output:
      - items: list of normalized dicts with keys:
        {
          uuid, custom_name_raw, custom_name, piece_key, color, letter,
          square_tag, pos:{x,y,z}, tags:[]
        }
    """

    @property
    def kind(self) -> str:
        return "normalize_entities"

    def run(self, items: Any = None, piece_tag_map: Optional[Dict[str, str]] = None, **kwargs) -> Dict[str, Any]:
        try:
            arr: List[Any] = items if isinstance(items, list) else []
            tag2letter = piece_tag_map or {
                "pawn": "P", "knight": "N", "bishop": "B",
                "rook": "R", "queen": "Q", "king": "K"
            }
            re_piece_key = re.compile(r"^[wb][PRNBQK]_[a-h][1-8]$")
            re_square = re.compile(r"^[a-h][1-8]$")

            out: List[Dict[str, Any]] = []
            for it in arr:
                if not isinstance(it, dict):
                    continue
                raw_name = it.get("custom_name") or it.get("name") or ""
                clean_name = self._clean_name(raw_name)
                tags = [t for t in (it.get("tags") or []) if isinstance(t, str)]
                # piece_key
                pk = None
                for t in tags:
                    if re_piece_key.match(t):
                        pk = t
                        break
                if not pk:
                    pk = clean_name or None
                # color / letter
                color, letter = None, None
                if pk and re_piece_key.match(pk):
                    color = pk[0]
                    letter = pk[1]
                else:
                    if "white" in tags:
                        color = "w"
                    if "black" in tags:
                        color = "b"
                    # infer letter by tag
                    for t in tags:
                        if t in tag2letter:
                            letter = tag2letter[t]
                            break
                # square_tag
                square_tag = None
                for t in tags:
                    if re_square.match(t):
                        square_tag = t
                        break
                # pos normalization
                pos = it.get("pos") or {}
                x = self._to_float(self._get(pos, "x"))
                y = self._to_float(self._get(pos, "y"))
                z = self._to_float(self._get(pos, "z"))
                norm = {
                    "uuid": it.get("uuid"),
                    "custom_name_raw": raw_name,
                    "custom_name": clean_name or None,
                    "piece_key": pk,
                    "color": color,
                    "letter": letter,
                    "square_tag": square_tag,
                    "pos": {"x": x, "y": y, "z": z} if x is not None and y is not None and z is not None else None,
                    "tags": tags,
                }
                out.append(norm)
            return {"items": out}
        except Exception as e:
            raise HandlerError(f"normalize_entities failed: {str(e)[:200]}", "NORMALIZE_ENTITIES_ERROR", "validation", False)

    def _clean_name(self, s: Any) -> str:
        txt = str(s or "").strip()
        # strip outer quotes 'name' or "name"
        if len(txt) >= 2 and ((txt[0] == txt[-1] == '"') or (txt[0] == txt[-1] == "'")):
            txt = txt[1:-1]
        # handle nested quotes like '"name"'
        if len(txt) >= 2 and ((txt[0] == '"' and txt[-1] == '"') or (txt[0] == "'" and txt[-1] == "'")):
            txt = txt[1:-1]
        return txt.strip()

    def _to_float(self, v: Any):
        try:
            return float(v)
        except Exception:
            return None

    def _get(self, obj: Any, key: str):
        try:
            if isinstance(obj, dict):
                return obj.get(key)
        except Exception:
            return None
        return None
