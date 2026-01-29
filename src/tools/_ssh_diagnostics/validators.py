"""SSH Diagnostics - Input validation"""
from typing import Dict, Any

OPERATIONS_REQUIRING_HOST = ["test_connection", "test_network", "generate_ssh_config"]


def validate_params(operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate operation parameters.
    
    Args:
        operation: Operation name
        params: Parameters to validate
        
    Returns:
        Empty dict if valid, error dict if invalid
    """
    # Check host requirement
    if operation in OPERATIONS_REQUIRING_HOST:
        if not params.get("host"):
            return {"error": f"Operation '{operation}' requires 'host' parameter"}
    
    # Validate host format (basic)
    if params.get("host"):
        host = params["host"]
        if not isinstance(host, str) or len(host) < 3:
            return {"error": "Invalid host format"}
    
    # Validate port range
    if params.get("port"):
        port = params["port"]
        if not isinstance(port, int) or port < 1 or port > 65535:
            return {"error": "Port must be between 1 and 65535"}
    
    # Validate log_lines
    if params.get("log_lines"):
        lines = params["log_lines"]
        if not isinstance(lines, int) or lines < 10 or lines > 500:
            return {"error": "log_lines must be between 10 and 500"}
    
    # Validate mtr_count
    if params.get("mtr_count"):
        count = params["mtr_count"]
        if not isinstance(count, int) or count < 10 or count > 200:
            return {"error": "mtr_count must be between 10 and 200"}
    
    # Validate timeout
    if params.get("timeout"):
        timeout = params["timeout"]
        if not isinstance(timeout, int) or timeout < 5 or timeout > 120:
            return {"error": "timeout must be between 5 and 120"}
    
    return {}
