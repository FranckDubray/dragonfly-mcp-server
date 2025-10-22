"""
Control player operation
"""
import logging
import time
from ..geometry import calculate_look_rotation
from ..utils import CommandBuilder

logger = logging.getLogger(__name__)

def control_player_op(params: dict, rcon, context: dict) -> dict:
    """Control player actions
    
    Args:
        params: {player_action, target_position, yaw, pitch, look_at, gamemode}
        rcon: RconClient
        context: {player_pos, player_rot, ...}
        
    Returns:
        {success, action, result, time_ms}
    """
    action = params.get('player_action')
    player_name = params.get('player_name', '@p')
    
    if not action:
        return {
            "success": False,
            "error": "player_action required"
        }
    
    try:
        start_time = time.time()
        
        if action == "teleport":
            result = _action_teleport(params, rcon, context, player_name)
        
        elif action == "look":
            result = _action_look(params, rcon, context, player_name)
        
        elif action == "gamemode":
            result = _action_gamemode(params, rcon, player_name)
        
        else:
            return {
                "success": False,
                "error": f"Unknown player_action: {action}"
            }
        
        elapsed = (time.time() - start_time) * 1000
        result['time_ms'] = elapsed
        result['action'] = action
        
        return result
    
    except Exception as e:
        logger.error(f"Control player failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "action": action
        }

def _action_teleport(params: dict, rcon, context: dict, player: str) -> dict:
    """Teleport player"""
    target = params.get('target_position')
    if not target:
        target = context.get('resolved_position', {'x': 0, 'y': 64, 'z': 0})
    
    yaw = params.get('yaw')
    pitch = params.get('pitch')
    
    cmd = CommandBuilder.tp(player, target['x'], target['y'], target['z'], yaw, pitch)
    response = rcon.execute(cmd)
    
    logger.info(f"Teleported {player} to ({target['x']:.1f}, {target['y']:.1f}, {target['z']:.1f})")
    
    return {
        "success": True,
        "target_position": target,
        "yaw": yaw,
        "pitch": pitch,
        "response": response
    }

def _action_look(params: dict, rcon, context: dict, player: str) -> dict:
    """Change player look direction"""
    player_pos = context.get('player_pos', {'x': 0, 'y': 64, 'z': 0})
    
    # Auto-calculate rotation if look_at provided
    if 'look_at' in params and params['look_at']:
        rotation = calculate_look_rotation(player_pos, params['look_at'])
        yaw = rotation['yaw']
        pitch = rotation['pitch']
    else:
        yaw = params.get('yaw', 0)
        pitch = params.get('pitch', 0)
    
    # Teleport to same position with new rotation
    cmd = CommandBuilder.tp(player, player_pos['x'], player_pos['y'], player_pos['z'], yaw, pitch)
    response = rcon.execute(cmd)
    
    logger.info(f"Changed {player} look direction: yaw={yaw:.1f}, pitch={pitch:.1f}")
    
    return {
        "success": True,
        "yaw": yaw,
        "pitch": pitch,
        "response": response
    }

def _action_gamemode(params: dict, rcon, player: str) -> dict:
    """Change player gamemode"""
    gamemode = params.get('gamemode')
    if not gamemode:
        return {
            "success": False,
            "error": "gamemode parameter required"
        }
    
    cmd = CommandBuilder.gamemode(gamemode, player)
    response = rcon.execute(cmd)
    
    logger.info(f"Changed {player} gamemode to {gamemode}")
    
    return {
        "success": True,
        "gamemode": gamemode,
        "player": player,
        "response": response
    }
