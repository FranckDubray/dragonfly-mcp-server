"""API routing layer for Légifrance LEGI operations."""
from __future__ import annotations
from typing import Dict, Any
import logging

from .validators import (
    validate_operation,
    validate_scope,
    validate_depth,
    validate_limit,
    validate_article_ids,
    validate_date
)
from .core import get_summary, get_article

LOG = logging.getLogger(__name__)


def route_request(operation: str, **params) -> Dict[str, Any]:
    """Route request to appropriate handler.
    
    Args:
        operation: Operation name
        **params: Operation parameters
        
    Returns:
        Operation result or error
    """
    # Validate operation
    op_validation = validate_operation(operation)
    if not op_validation["valid"]:
        LOG.warning(f"Invalid operation: {op_validation['error']}")
        return {"error": op_validation["error"]}
    
    operation = op_validation["operation"]
    
    # Route to handler
    if operation == "get_summary":
        return handle_get_summary(**params)
    
    elif operation == "get_article":
        return handle_get_article(**params)
    
    else:
        return {"error": f"Unknown operation: {operation}"}


def handle_get_summary(**params) -> Dict[str, Any]:
    """Handle get_summary operation.
    
    Args:
        **params: Summary parameters (scope, depth, limit)
        
    Returns:
        Summary data or error
    """
    # Validate scope
    scope_validation = validate_scope(params.get("scope"))
    if not scope_validation["valid"]:
        LOG.warning(f"Invalid scope: {scope_validation['error']}")
        return {"error": scope_validation["error"]}
    
    scope = scope_validation["scope"]
    
    # Validate depth
    depth_validation = validate_depth(params.get("depth"))
    if not depth_validation["valid"]:
        LOG.warning(f"Invalid depth: {depth_validation['error']}")
        return {"error": depth_validation["error"]}
    
    depth = depth_validation["depth"]
    
    # Validate limit
    limit_validation = validate_limit(params.get("limit"))
    if not limit_validation["valid"]:
        LOG.warning(f"Invalid limit: {limit_validation['error']}")
        return {"error": limit_validation["error"]}
    
    limit = limit_validation["limit"]
    
    # Log operation
    LOG.info(f"📊 get_summary: scope={scope}, depth={depth}, limit={limit}")
    
    # Execute
    return get_summary(scope=scope, depth=depth, limit=limit)


def handle_get_article(**params) -> Dict[str, Any]:
    """Handle get_article operation.
    
    Args:
        **params: Article parameters (article_ids, date, include_*)
        
    Returns:
        Articles data or error
    """
    # Validate article_ids
    ids_validation = validate_article_ids(params.get("article_ids"))
    if not ids_validation["valid"]:
        LOG.warning(f"Invalid article_ids: {ids_validation['error']}")
        return {"error": ids_validation["error"]}
    
    article_ids = ids_validation["article_ids"]
    
    # Validate date
    date_validation = validate_date(params.get("date"))
    if not date_validation["valid"]:
        LOG.warning(f"Invalid date: {date_validation['error']}")
        return {"error": date_validation["error"]}
    
    date = date_validation["date"]
    
    # Get include flags
    include_links = params.get("include_links", True)
    include_breadcrumb = params.get("include_breadcrumb", True)
    
    # Log operation
    LOG.info(f"📄 get_article: {len(article_ids)} articles, date={date}, links={include_links}, breadcrumb={include_breadcrumb}")
    
    # Execute
    return get_article(
        article_ids=article_ids,
        date=date,
        include_links=include_links,
        include_breadcrumb=include_breadcrumb
    )
