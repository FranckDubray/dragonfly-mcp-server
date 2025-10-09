from typing import Any, Dict, List, Optional
import os
import json
import re

from ._image_genedit.core import run_image_op


def _coerce_to_list(val: Any) -> Optional[List[str]]:
    """Coerce various UI inputs into a list of strings.
    - If already a list -> clean and return
    - If JSON array in string -> parse and return
    - If single string -> split on commas/whitespace/newlines, or wrap as single-item list
    - None/empty -> None/[]
    """
    if val is None:
        return None
    if isinstance(val, list):
        out = [str(x).strip() for x in val if isinstance(x, (str, int, float)) and str(x).strip()]
        return out
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return []
        # Try JSON array
        try:
            j = json.loads(s)
            if isinstance(j, list):
                return [str(x).strip() for x in j if isinstance(x, (str, int, float)) and str(x).strip()]
        except Exception:
            pass
        # Split on commas/whitespace/newlines
        parts = [p.strip() for p in re.split(r"[\s,]+", s) if p.strip()]
        if parts:
            return parts
        return [s]
    # Fallback: wrap non-string scalars
    return [str(val).strip()]


def run(operation: str = "run", **params) -> Dict[str, Any]:
    """
    Facade pour l'outil generate_edit_image.
    Paramètres attendus:
      - operation: "generate" | "edit"
      - prompt: str
      - images: list[str] (data URLs) OU image_urls: list[str] (alias http(s)/data/base64), requis pour edit (1..3)
      - format: "png" | "jpg" (def: png)
      - ratio: str (ex: "1:1")
      - width: int
      - height: int
      - n: int (def: 4)
      - debug: bool
    """
    # Récupération robuste de l'opération (cf. LLM_DEV_GUIDE: éviter le conflit d'argument "operation")
    op = params.pop("operation", operation)
    if op not in ("generate", "edit"):
        return {"error": "Invalid or missing 'operation' (expected 'generate' or 'edit')"}

    if not params.get("prompt"):
        return {"error": "Missing required parameter: prompt"}

    if op == "edit":
        # Coercion des champs UI en liste
        imgs = _coerce_to_list(params.get("images"))
        alt = _coerce_to_list(params.get("image_urls"))
        has_images = isinstance(imgs, list) and len(imgs) > 0
        has_alt = isinstance(alt, list) and len(alt) > 0
        if not (has_images or has_alt):
            return {"error": "'images' is required for operation=edit (accepts http(s), data:URL, or base64 via alias 'image_urls')"}
        # Normaliser: on privilégie images si présent, sinon image_urls
        use_list = imgs if has_images else alt
        # Limite 1..3
        if len(use_list) > 3:
            return {"error": "Too many images for edit (max 3)"}
        # Injecter côté params pour la core API
        params["images"] = use_list
        # Nettoyer alias pour éviter les confusions
        params.pop("image_urls", None)

    try:
        return run_image_op(operation=op, **params)
    except Exception as e:
        return {"error": f"generate_edit_image failed: {e}"}


def spec() -> Dict[str, Any]:
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'generate_edit_image.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)
