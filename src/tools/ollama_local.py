"""
Ollama Local + Web Search tool.
Interface complète avec Ollama local et recherche web cloud.
"""
from ._ollama_local.api import route_operation
from ._ollama_local import spec as _spec


def run(operation: str = None, **params):
    """
    Execute Ollama operation (local or web search).
    
    Args:
        operation: Operation name (list_models, generate, chat, web_search, etc.)
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
