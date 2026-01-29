"""Validation logic for Légifrance LEGI parameters v2."""
from __future__ import annotations
from typing import Dict, Any
import re
from datetime import datetime


def validate_operation(operation: str) -> Dict[str, Any]:
    if not operation:
        return {"valid": False, "error": "operation is required"}

    valid_operations = ["list_codes", "get_code", "get_articles"]
    operation = operation.strip().lower()

    if operation not in valid_operations:
        return {
            "valid": False,
            "error": f"Invalid operation '{operation}'. Must be one of: {', '.join(valid_operations)}"
        }

    return {"valid": True, "operation": operation}


def validate_scope(scope: str = None) -> Dict[str, Any]:
    if scope is None:
        scope = "codes_en_vigueur"

    valid_scopes = ["codes_en_vigueur", "codes_abroges", "all"]
    scope = scope.strip().lower()

    if scope not in valid_scopes:
        return {
            "valid": False,
            "error": f"Invalid scope '{scope}'. Must be one of: {', '.join(valid_scopes)}"
        }

    return {"valid": True, "scope": scope}


def validate_nature(nature: str = None) -> Dict[str, Any]:
    """Validate nature parameter for filtering by text type."""
    if nature is None:
        nature = "CODE"

    valid_natures = ["CODE", "ARRETE", "DECRET", "LOI", "ORDONNANCE", "ALL"]
    nature = nature.strip().upper()

    if nature not in valid_natures:
        return {
            "valid": False,
            "error": f"Invalid nature '{nature}'. Must be one of: {', '.join(valid_natures)}"
        }

    return {"valid": True, "nature": nature}


def validate_code_id(code_id: Any) -> Dict[str, Any]:
    if not code_id:
        return {"valid": False, "error": "code_id is required for get_code operation"}

    if not isinstance(code_id, str):
        return {
            "valid": False,
            "error": f"code_id must be a string (got {type(code_id).__name__})"
        }

    code_id_pattern = re.compile(r"^LEGITEXT\d{12}$")
    if not code_id_pattern.match(code_id):
        return {
            "valid": False,
            "error": f"Invalid code_id format. Must be 'LEGITEXT' + 12 digits (got '{code_id}')"
        }

    return {"valid": True, "code_id": code_id}


def validate_root_section_id(root_section_id: Any) -> Dict[str, Any]:
    if root_section_id is None:
        return {"valid": True, "root_section_id": None}

    if not isinstance(root_section_id, str):
        return {
            "valid": False,
            "error": f"root_section_id must be a string (got {type(root_section_id).__name__})"
        }

    pattern = re.compile(r"^LEGISCTA\d{12}$")
    if not pattern.match(root_section_id):
        return {
            "valid": False,
            "error": f"Invalid root_section_id format. Must be 'LEGISCTA' + 12 digits (got '{root_section_id}')"
        }

    return {"valid": True, "root_section_id": root_section_id}


def validate_depth(depth: Any = None) -> Dict[str, Any]:
    if depth is None:
        return {"valid": True, "depth": 3}

    try:
        depth = int(depth)
    except (ValueError, TypeError):
        return {"valid": False, "error": f"depth must be an integer (got {type(depth).__name__})"}

    if not 1 <= depth <= 10:
        return {"valid": False, "error": f"depth must be between 1 and 10 (got {depth})"}

    return {"valid": True, "depth": depth}


def validate_article_ids(article_ids: Any) -> Dict[str, Any]:
    if not article_ids:
        return {"valid": False, "error": "article_ids is required for get_articles operation"}

    if not isinstance(article_ids, list):
        return {
            "valid": False,
            "error": f"article_ids must be a list (got {type(article_ids).__name__})"
        }

    if len(article_ids) == 0:
        return {"valid": False, "error": "article_ids must contain at least 1 article ID"}

    if len(article_ids) > 50:
        return {
            "valid": False,
            "error": f"article_ids must contain at most 50 article IDs (got {len(article_ids)})"
        }

    article_id_pattern = re.compile(r"^LEGIARTI\d{12}$")
    invalid_ids = []

    for article_id in article_ids:
        if not isinstance(article_id, str):
            return {
                "valid": False,
                "error": f"All article IDs must be strings (got {type(article_id).__name__})"
            }

        if not article_id_pattern.match(article_id):
            invalid_ids.append(article_id)

    if invalid_ids:
        examples = invalid_ids[:3]
        return {
            "valid": False,
            "error": f"Invalid article ID format. Must be 'LEGIARTI' + 12 digits. Invalid: {examples}"
        }

    return {"valid": True, "article_ids": article_ids}


def validate_date(date: str = None) -> Dict[str, Any]:
    if date is None:
        return {"valid": True, "date": datetime.now().strftime("%Y-%m-%d")}

    if not isinstance(date, str):
        return {"valid": False, "error": f"date must be a string (got {type(date).__name__})"}

    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    if not date_pattern.match(date):
        return {
            "valid": False,
            "error": f"date must be in format YYYY-MM-DD (got '{date}')"
        }

    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError as e:
        return {"valid": False, "error": f"Invalid date: {e}"}

    return {"valid": True, "date": date}
