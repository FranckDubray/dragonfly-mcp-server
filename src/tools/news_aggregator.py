"""
News Aggregator tool.
Multi-source news aggregation (NewsAPI, NYT, Guardian).
Search, top headlines, sources listing with unified output.
"""
from ._news_aggregator.api import route_operation
from ._news_aggregator import spec as _spec


def run(operation: str = None, **params):
    """
    Execute news aggregator operation.
    
    Args:
        operation: Operation name (search_news, top_headlines, list_sources)
        **params: Operation parameters
        
    Returns:
        Dict with operation result or error
    """
    # Extract operation
    op = (operation or params.get("operation", "")).strip().lower()
    
    if not op:
        return {"error": "Parameter 'operation' is required"}
    
    # Remove operation from params to avoid conflicts
    if "operation" in params:
        del params["operation"]
    
    # Route to appropriate handler
    return route_operation(op, **params)


def spec():
    """Return tool specification."""
    return _spec()
