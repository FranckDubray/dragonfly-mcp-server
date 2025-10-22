"""
Core orchestration
"""
import logging
from .client import RconClient
from .utils import validate_params
from .geometry import resolve_position
from . import operations

logger = logging.getLogger(__name__)

# Operation routing map
OPERATION_MAP = {
    "execute_command": operations.execute_command_op,
    "spawn_entities": operations.spawn_entities_op,
    "build_structure": operations.build_structure_op,
    "import_3d_model": operations.import_3d_model_op,
    "control_player": operations.control_player_op,
    "set_environment": operations.set_environment_op,
    "batch_commands": operations.batch_commands_op,
    "get_player_state": operations.get_player_state_op,
    "render_image": operations.render_image_op,
}

def execute_with_rcon(operation: str, params: dict) -> dict:
    """Execute operation with RCON connection management
    
    Args:
        operation: Operation name
        params: Validated parameters
        
    Returns:
        Operation result dict
    """
    try:
        # Validate params
        validated_params = validate_params(operation, params)
        
        # Connect to RCON
        try:
            with RconClient() as rcon:
                # Test connection
                if not rcon.test_connection():
                    return {
                        "success": False,
                        "error": "RCON connection test failed (server may not have RCON enabled)",
                        "operation": operation,
                        "hint": "Enable RCON in server.properties: enable-rcon=true, rcon.port=25575"
                    }
                
                # Prepare context
                context = prepare_context(validated_params, rcon)
                
                # Route to operation handler
                handler = OPERATION_MAP.get(operation)
                if not handler:
                    return {
                        "success": False,
                        "error": f"Unknown operation: {operation}",
                        "operation": operation
                    }
                
                # Execute operation
                result = handler(validated_params, rcon, context)
                result['operation'] = operation
                
                return result
        
        except Exception as e:
            # More detailed error for RCON connection issues
            error_msg = str(e)
            logger.error(f"RCON connection failed: {error_msg}", exc_info=True)
            
            return {
                "success": False,
                "error": f"RCON connection failed: {error_msg}",
                "error_type": type(e).__name__,
                "operation": operation,
                "hint": "Check that Minecraft server is running with RCON enabled (server.properties)"
            }
    
    except Exception as e:
        logger.error(f"Operation failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "operation": operation
        }

def prepare_context(params: dict, rcon: RconClient) -> dict:
    """Prepare execution context
    
    Fetches player state if needed for relative positioning and resolves base position.
    """
    context = {}

    # Defaults
    context['player_pos'] = {'x': 0, 'y': 64, 'z': 0}
    context['player_rot'] = {'yaw': 0, 'pitch': 0}

    needs_relative = params.get('relative_to_player', True)

    # Fetch player state if relative positioning needed or player action
    if needs_relative or 'player_action' in params:
        try:
            player_name = params.get('player_name', '@p')
            player_data = rcon.get_player_data(player_name)

            if 'Pos' in player_data:
                context['player_pos'] = player_data['Pos']
            if 'Rotation' in player_data:
                context['player_rot'] = player_data['Rotation']
        except Exception as e:
            logger.warning(f"Failed to fetch player state: {e}, using defaults")

    # Always resolve a base position (respects absolute params.position when provided)
    try:
        context['resolved_position'] = resolve_position(
            params,
            context['player_pos'],
            context['player_rot']
        )
    except Exception:
        # Fallback to player_pos
        context['resolved_position'] = dict(context['player_pos'])

    return context
