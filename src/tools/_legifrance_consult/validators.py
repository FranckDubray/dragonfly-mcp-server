"""Validation logic."""
from typing import Dict, Any, List
import re

def validate_operation(operation: str) -> Dict[str, Any]:
    valid = ["search_sections", "get_section_tree", "get_articles"]
    if operation not in valid:
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
    if len(ids) > 50:
        return {"valid": False, "error": "Max 50 articles"}
    return {"valid": True, "article_ids": ids}
