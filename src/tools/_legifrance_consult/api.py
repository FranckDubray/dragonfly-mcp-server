"""API Routing."""
from typing import Dict, Any
from .core import execute_ssh
from .validators import (
    validate_operation,
    validate_section_tree_params,
    validate_article_ids,
)

def route_request(operation: str, **params) -> Dict[str, Any]:
    val = validate_operation(operation)
    if not val["valid"]:
        return {"error": val["error"]}

    # Anti-overload: validate get_section_tree params
    if operation == "get_section_tree":
        tree_val = validate_section_tree_params(**params)
        if not tree_val["valid"]:
            return {"error": tree_val["error"]}
        params = tree_val["params"]

    # Validate article_ids
    if operation == "get_articles":
        ids = params.get("ids") or params.get("article_ids") or []
        art_val = validate_article_ids(ids)
        if not art_val["valid"]:
            return {"error": art_val["error"]}

    return execute_ssh(operation, **params)
