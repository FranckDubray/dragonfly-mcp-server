"""
Bootstrap for generate_edit_image tool.
Simplified with proper input validation delegation.
"""
from typing import Any, Dict
import os
import json

from ._image_genedit.core import run_image_op
from ._image_genedit.validators import normalize_image_inputs, coerce_to_list


def run(operation: str = "run", **params) -> Dict[str, Any]:
    """
    Facade pour l'outil generate_edit_image.
    
    Paramètres attendus:
      - operation: "generate" | "edit"
      - prompt: str
      - images: list[str] (data URLs) OU image_urls: list[str] (alias), requis pour edit (1..3)
      - n: int (def: 4)
      - debug: bool
    """
    # Récupération robuste de l'opération
    op = params.pop("operation", operation)
    if op not in ("generate", "edit"):
        return {"error": "Invalid or missing 'operation' (expected 'generate' or 'edit')"}

    if not params.get("prompt"):
        return {"error": "Missing required parameter: prompt"}

    # Coercion des champs UI en liste
    imgs = coerce_to_list(params.get("images"))
    alt = coerce_to_list(params.get("image_urls"))
    
    # Pour edit : normaliser les images
    normalized_images = None
    if op == "edit":
        # Privilégier images si présent, sinon image_urls
        raw_list = imgs if imgs else alt
        
        if not raw_list:
            return {"error": "'images' is required for operation=edit (accepts http(s), data:URL, or base64 via alias 'image_urls')"}
        
        # Normalisation (http(s) → data URL, validation)
        normalized_images, err = normalize_image_inputs(raw_list)
        if err:
            return {"error": f"Image validation failed: {err}"}
    
    try:
        return run_image_op(
            operation=op,
            prompt=params["prompt"],
            images=normalized_images,
            n=params.get("n"),
            debug=params.get("debug", False),
        )
    except Exception as e:
        return {"error": f"generate_edit_image failed: {e}"}


def spec() -> Dict[str, Any]:
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'generate_edit_image.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)
