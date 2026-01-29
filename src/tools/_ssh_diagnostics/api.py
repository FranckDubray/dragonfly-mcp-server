"""SSH Diagnostics - API routing"""
from typing import Dict, Any
import logging

from .core import (
    test_connection,
    check_server_logs,
    check_keepalive_config,
    test_network,
    check_firewall,
    check_fail2ban,
    check_server_load,
    generate_ssh_config,
    full_diagnostic
)
from .validators import validate_params

logger = logging.getLogger(__name__)

OPERATIONS = {
    "test_connection": test_connection,
    "check_server_logs": check_server_logs,
    "check_keepalive_config": check_keepalive_config,
    "test_network": test_network,
    "check_firewall": check_firewall,
    "check_fail2ban": check_fail2ban,
    "check_server_load": check_server_load,
    "generate_ssh_config": generate_ssh_config,
    "full_diagnostic": full_diagnostic,
}


def route_request(operation: str, **params) -> Dict[str, Any]:
    """Route request to appropriate handler.
    
    Args:
        operation: Operation to perform
        **params: Operation parameters
        
    Returns:
        Operation result
    """
    try:
        # Validate params
        validation = validate_params(operation, params)
        if "error" in validation:
            return validation
        
        # Get handler
        handler = OPERATIONS.get(operation)
        if not handler:
            return {"error": f"Unknown operation: {operation}"}
        
        # Execute
        logger.info(f"SSH diagnostics: {operation}")
        result = handler(**params)
        
        return result
        
    except Exception as e:
        logger.error(f"SSH diagnostics error ({operation}): {e}", exc_info=True)
        return {"error": f"Diagnostic failed: {str(e)}"}
