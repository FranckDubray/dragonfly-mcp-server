"""API routing for Ollama operations."""
from .core import (
    handle_list_models,
    handle_get_version,
    handle_get_running_models,
    handle_show_model,
    handle_pull_model,
    handle_push_model,
    handle_create_model,
    handle_copy_model,
    handle_delete_model,
    handle_generate,
    handle_chat,
    handle_embeddings,
    handle_web_search,
    handle_chat_with_web
)


def route_operation(operation: str, **params):
    """
    Route operation to appropriate handler.
    
    Args:
        operation: Operation name
        **params: Operation parameters
        
    Returns:
        Dict with result or error
    """
    # Operation mapping
    operations = {
        # Model management
        "list_models": handle_list_models,
        "get_version": handle_get_version,
        "get_running_models": handle_get_running_models,
        "show_model": handle_show_model,
        "pull_model": handle_pull_model,
        "push_model": handle_push_model,
        "create_model": handle_create_model,
        "copy_model": handle_copy_model,
        "delete_model": handle_delete_model,
        
        # Text generation
        "generate": handle_generate,
        "chat": handle_chat,
        "embeddings": handle_embeddings,
        
        # Web search
        "web_search": handle_web_search,
        "chat_with_web": handle_chat_with_web,
    }
    
    handler = operations.get(operation)
    if not handler:
        available_ops = ", ".join(sorted(operations.keys()))
        return {
            "error": f"Unknown operation '{operation}'. Available: {available_ops}"
        }
    
    try:
        return handler(**params)
    except Exception as e:
        return {
            "error": f"Handler error for '{operation}': {str(e)}",
            "operation": operation
        }