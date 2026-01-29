"""API routing layer for SSH Client."""
from __future__ import annotations
from typing import Dict, Any

from .core import execute_command, check_status
from .sftp import upload_file, download_file


def route_operation(operation: str, **params) -> Dict[str, Any]:
    """Route SSH operation to appropriate handler.
    
    Args:
        operation: Operation type (exec, upload, download, status)
        **params: Operation parameters
        
    Returns:
        Operation result or error
    """
    try:
        if operation == "exec":
            return execute_command(**params)
        
        elif operation == "upload":
            return upload_file(**params)
        
        elif operation == "download":
            return download_file(**params)
        
        elif operation == "status":
            return check_status(**params)
        
        else:
            return {
                "error": f"Unknown operation: {operation}",
                "error_type": "invalid_operation"
            }
    
    except Exception as e:
        return {
            "error": f"Operation failed: {str(e)}",
            "error_type": "unknown",
            "operation": operation
        }
