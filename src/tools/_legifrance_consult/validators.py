"""Validation logic."""
from typing import Dict, Any, List
import re

VALID_OPERATIONS = [
    "list_codes", "search_sections", "get_section_tree", "get_articles"
]

def validate_operation(operation: str) -> Dict[str, Any]:
    if operation not in VALID_OPERATIONS:
        return {"valid": False, "error": f"Invalid operation: {operation}"}
    return {"valid": True, "operation": operation}

def validate_code_id(code_id: str) -> Dict[str, Any]:
    if not code_id:
        return {"valid": True, "code_id": None}
    if not re.match(r"^LEGITEXT[0-9]{12}$", code_id):
        return {"valid": False, "error": "Invalid code_id format"}
    return {"valid": True, "code_id": code_id}

def validate_article_ids(ids: List[str]) -> Dict[str, Any]:
    if not ids:
        return {"valid": False, "error": "article_ids required"}
    if len(ids) > 25:
        return {"valid": False, "error": "Max 25 articles per call"}
    return {"valid": True, "article_ids": ids}

def validate_section_tree_params(**params) -> Dict[str, Any]:
    """Anti-overload protection for get_section_tree."""
    depth = params.get("max_depth", 4)
    section_id = params.get("section_id")
    max_size_kb = params.get("max_size_kb")

    # RULE 1: depth > 2 without section_id = explosion guaranteed
    if depth > 2 and not section_id:
        return {
            "valid": False,
            "error": (
                f"max_depth={depth} without section_id is forbidden "
                "(risk of ContextTooLarge). Use max_depth=2 for discovery, "
                "then target a specific section_id for deeper exploration."
            )
        }

    # RULE 2: force max_size_kb if not provided
    if not max_size_kb:
        params["max_size_kb"] = 300 if not section_id else 500

    return {"valid": True, "params": params}
