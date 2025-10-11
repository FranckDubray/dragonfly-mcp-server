"""
Trivia API routing
Entry point for operation routing with error handling
"""
from typing import Dict, Any
from .validators import (
    validate_operation,
    validate_get_questions_params,
    validate_category_count_params,
    validate_reset_token_params
)
from .services.api_client import TriviaAPIClient, TriviaAPIError
from . import core


def route_operation(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route operation to appropriate handler with comprehensive error handling
    
    Args:
        params: Tool parameters including operation
    
    Returns:
        Operation result
    """
    try:
        # Validate operation parameter
        operation = params.get("operation")
        if not operation:
            return {
                "success": False,
                "error": "Missing required parameter: operation"
            }
        
        validate_operation(operation)
        
        # Initialize API client
        client = TriviaAPIClient()
        
        # Route to appropriate handler
        if operation == "get_questions":
            validate_get_questions_params(params)
            return core.get_questions(params, client)
        
        elif operation == "list_categories":
            return core.list_categories(client)
        
        elif operation == "get_category_count":
            validate_category_count_params(params)
            return core.get_category_count(params, client)
        
        elif operation == "get_global_count":
            return core.get_global_count(client)
        
        elif operation == "create_session_token":
            return core.create_session_token(client)
        
        elif operation == "reset_session_token":
            validate_reset_token_params(params)
            return core.reset_session_token(params, client)
        
        else:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}"
            }
    
    except ValueError as e:
        return {
            "success": False,
            "error": f"Validation error: {str(e)}"
        }
    
    except TypeError as e:
        return {
            "success": False,
            "error": f"Type error: {str(e)}"
        }
    
    except TriviaAPIError as e:
        return {
            "success": False,
            "error": f"API error: {str(e)}"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }
