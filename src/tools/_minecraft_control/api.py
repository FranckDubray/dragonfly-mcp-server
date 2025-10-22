"""
API router - main entry point
"""
import logging
from .core import execute_with_rcon

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def execute_operation(**params) -> dict:
    """Main entry point for minecraft_control tool
    
    Args:
        operation: str - Operation to execute
        **params: Operation-specific parameters
        
    Returns:
        dict: Standardized result
            {
                "success": bool,
                "operation": str,
                "result": Any,
                "stats": dict,
                "warnings": list[str]
            }
    """
    operation = params.get('operation')
    
    if not operation:
        return {
            "success": False,
            "error": "operation parameter required",
            "available_operations": [
                "execute_command",
                "spawn_entities",
                "build_structure",
                "import_3d_model",
                "control_player",
                "set_environment",
                "batch_commands",
                "get_player_state"
            ]
        }
    
    try:
        logger.info(f"Executing operation: {operation}")
        
        # Execute with RCON
        result = execute_with_rcon(operation, params)
        
        # Standardize output format
        return _standardize_output(result)
    
    except Exception as e:
        logger.error(f"Execution failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "operation": operation
        }

def _standardize_output(result: dict) -> dict:
    """Standardize operation output format
    
    Ensures consistent structure across all operations
    """
    standardized = {
        "success": result.get('success', False),
        "operation": result.get('operation', 'unknown')
    }
    
    # Extract stats
    stats = {}
    if 'time_ms' in result:
        stats['time_ms'] = result['time_ms']
    if 'executed_count' in result:
        stats['executed_count'] = result['executed_count']
    if 'spawned_count' in result:
        stats['spawned_count'] = result['spawned_count']
    if 'blocks_placed' in result:
        stats['blocks_placed'] = result['blocks_placed']
    if 'chunks_count' in result:
        stats['chunks_count'] = result['chunks_count']
    
    if stats:
        standardized['stats'] = stats
    
    # Extract warnings
    if 'warnings' in result and result['warnings']:
        standardized['warnings'] = result['warnings']
    
    # Extract error
    if 'error' in result:
        standardized['error'] = result['error']
        if 'error_type' in result:
            standardized['error_type'] = result['error_type']
    
    # Add remaining result data
    for key, value in result.items():
        if key not in ['success', 'operation', 'time_ms', 'warnings', 'error', 'error_type',
                       'executed_count', 'spawned_count', 'blocks_placed', 'chunks_count']:
            if 'result' not in standardized:
                standardized['result'] = {}
            standardized['result'][key] = value
    
    return standardized
