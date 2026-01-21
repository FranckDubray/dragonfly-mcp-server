"""Validation logic for Légifrance LEGI parameters."""
from __future__ import annotations
from typing import Dict, Any, List
import re
from datetime import datetime


def validate_operation(operation: str) -> Dict[str, Any]:
    """Validate operation parameter.
    
    Args:
        operation: Operation name
        
    Returns:
        {"valid": bool, "operation": str, "error": str}
    """
    if not operation:
        return {"valid": False, "error": "operation is required"}
    
    valid_operations = ["get_summary", "get_article"]
    operation = operation.strip().lower()
    
    if operation not in valid_operations:
        return {
            "valid": False,
            "error": f"Invalid operation '{operation}'. Must be one of: {', '.join(valid_operations)}"
        }
    
    return {"valid": True, "operation": operation}


def validate_scope(scope: str = None) -> Dict[str, Any]:
    """Validate scope parameter for get_summary.
    
    Args:
        scope: Scope (codes_en_vigueur, codes_abroges, all)
        
    Returns:
        {"valid": bool, "scope": str, "error": str}
    """
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


def validate_depth(depth: Any = None) -> Dict[str, Any]:
    """Validate depth parameter for get_summary.
    
    Args:
        depth: Depth level (1-5)
        
    Returns:
        {"valid": bool, "depth": int, "error": str}
    """
    if depth is None:
        return {"valid": True, "depth": 2}
    
    try:
        depth = int(depth)
    except (ValueError, TypeError):
        return {"valid": False, "error": f"depth must be an integer (got {type(depth).__name__})"}
    
    if not 1 <= depth <= 5:
        return {"valid": False, "error": f"depth must be between 1 and 5 (got {depth})"}
    
    return {"valid": True, "depth": depth}


def validate_limit(limit: Any = None) -> Dict[str, Any]:
    """Validate limit parameter for get_summary.
    
    Args:
        limit: Max number of codes
        
    Returns:
        {"valid": bool, "limit": int, "error": str}
    """
    if limit is None:
        return {"valid": True, "limit": 77}
    
    try:
        limit = int(limit)
    except (ValueError, TypeError):
        return {"valid": False, "error": f"limit must be an integer (got {type(limit).__name__})"}
    
    if not 1 <= limit <= 200:
        return {"valid": False, "error": f"limit must be between 1 and 200 (got {limit})"}
    
    return {"valid": True, "limit": limit}


def validate_article_ids(article_ids: Any) -> Dict[str, Any]:
    """Validate article_ids parameter for get_article.
    
    Args:
        article_ids: List of article IDs
        
    Returns:
        {"valid": bool, "article_ids": List[str], "error": str}
    """
    if not article_ids:
        return {"valid": False, "error": "article_ids is required for get_article operation"}
    
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
    
    # Validate format: LEGIARTI + 12 digits
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
    """Validate date parameter for get_article.
    
    Args:
        date: Date string (YYYY-MM-DD)
        
    Returns:
        {"valid": bool, "date": str, "error": str}
    """
    if date is None:
        # Default: today
        return {"valid": True, "date": datetime.now().strftime("%Y-%m-%d")}
    
    if not isinstance(date, str):
        return {"valid": False, "error": f"date must be a string (got {type(date).__name__})"}
    
    # Validate format YYYY-MM-DD
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    if not date_pattern.match(date):
        return {
            "valid": False,
            "error": f"date must be in format YYYY-MM-DD (got '{date}')"
        }
    
    # Validate actual date
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError as e:
        return {"valid": False, "error": f"Invalid date: {e}"}
    
    return {"valid": True, "date": date}
