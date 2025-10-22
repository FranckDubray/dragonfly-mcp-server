"""
Get player state operation
"""
import logging
import time

logger = logging.getLogger(__name__)

def get_player_state_op(params: dict, rcon, context: dict) -> dict:
    """Get player position, rotation, and state
    
    Args:
        params: {player_name: str}
        rcon: RconClient
        context: Execution context
        
    Returns:
        {success, player, position, rotation, time_ms}
    """
    player_name = params.get('player_name', '@p')
    
    try:
        start_time = time.time()
        
        # Get player data via RCON
        logger.info(f"Getting state for player: {player_name}")
        data = rcon.get_player_data(player_name)
        
        elapsed = (time.time() - start_time) * 1000
        
        if not data:
            return {
                "success": False,
                "error": "Failed to retrieve player data",
                "player": player_name
            }
        
        result = {
            "success": True,
            "player": player_name,
            "time_ms": elapsed
        }
        
        # Add position if available
        if 'Pos' in data:
            result['position'] = data['Pos']
        
        # Add rotation if available
        if 'Rotation' in data:
            result['rotation'] = data['Rotation']
        
        logger.info(f"Retrieved state for {player_name}: pos={data.get('Pos')}, rot={data.get('Rotation')}")
        
        return result
    
    except Exception as e:
        logger.error(f"Get player state failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "player": player_name
        }
