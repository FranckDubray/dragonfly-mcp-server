"""
Bootstrap for generate_edit_image tool.
Simplified with proper input validation delegation.
"""
from typing import Any, Dict
import os
import json

from ._image_genedit.core import run_image_op
from ._image_genedit.validators import normalize_image_inputs, coerce_to_list, load_local_images


def run(operation: str = "run", **params) -> Dict[str, Any]:
    """
    Facade pour l'outil generate_edit_image.
    
    Paramètres attendus:
      - operation: "generate" | "edit"
      - prompt: str
      - images: list[str] (URLs http(s), data URLs, ou base64 brut) OU image_urls: list[str] (alias)
      - image_files: list[str] (paths relatifs à ./docs, ex: "test.png", "images/photo.jpg")
      - n: int (def: 4)
      - debug: bool
    
    Notes:
      - images et image_files peuvent être combinés (max 3 au total)
      - Pour edit: au moins une image (images OU image_files) est requise
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
    files = coerce_to_list(params.get("image_files"))
    
    # Pour edit : normaliser les images
    normalized_images = None
    if op == "edit":
        combined_images: list[str] = []
        
        # 1) Load local files first
        if files:
            local_data_urls, err = load_local_images(files)
            if err:
                return {"error": f"Failed to load image_files: {err}"}
            combined_images.extend(local_data_urls)
        
        # 2) Add remote URLs/data URLs/base64
        remote_list = imgs if imgs else alt
        if remote_list:
            normalized_remote, err = normalize_image_inputs(remote_list)
            if err:
                return {"error": f"Failed to normalize images: {err}"}
            combined_images.extend(normalized_remote)
        
        # 3) Validate total count
        if not combined_images:
            return {"error": "'images' or 'image_files' is required for operation=edit"}
        
        if len(combined_images) > 3:
            return {"error": f"Too many images: {len(combined_images)} (max 3). Reduce images or image_files."}
        
        normalized_images = combined_images
    
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
