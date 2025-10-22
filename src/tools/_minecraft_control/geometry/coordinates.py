"""
Coordinate calculations
"""
import logging
import math

logger = logging.getLogger(__name__)

def resolve_position(params: dict, player_pos: dict, player_rot: dict = None) -> dict:
    """Resolve absolute position from params
    
    Args:
        params: Operation params (may contain position/offset/relative_to_player)
        player_pos: Current player position {x, y, z}
        player_rot: Player rotation {yaw, pitch} (optional)
        
    Returns:
        Absolute position {x, y, z}
    """
    # Explicit absolute position
    if 'position' in params and params['position']:
        return params['position']
    
    # Relative to player
    if params.get('relative_to_player', True):
        offset = params.get('offset', {})
        return calculate_relative_position(
            player_pos, 
            player_rot or {'yaw': 0, 'pitch': 0},
            offset
        )
    
    # Default: player position
    return player_pos.copy()

def calculate_relative_position(base_pos: dict, rotation: dict, offset: dict) -> dict:
    """Calculate position relative to base with rotation
    
    Args:
        base_pos: Base position {x, y, z}
        rotation: {yaw, pitch} in degrees
        offset: {forward, up, right} in blocks
        
    Returns:
        Calculated position {x, y, z}
    """
    forward = offset.get('forward', 0)
    up = offset.get('up', 0)
    right = offset.get('right', 0)
    
    yaw_rad = math.radians(rotation['yaw'])
    
    # Calculate offset in world coordinates
    # Forward: along yaw direction
    # Right: perpendicular to yaw
    dx = -forward * math.sin(yaw_rad) + right * math.cos(yaw_rad)
    dz = forward * math.cos(yaw_rad) + right * math.sin(yaw_rad)
    dy = up
    
    return {
        'x': base_pos['x'] + dx,
        'y': base_pos['y'] + dy,
        'z': base_pos['z'] + dz
    }

def distance_3d(pos1: dict, pos2: dict) -> float:
    """Calculate 3D distance between positions"""
    dx = pos2['x'] - pos1['x']
    dy = pos2['y'] - pos1['y']
    dz = pos2['z'] - pos1['z']
    return math.sqrt(dx*dx + dy*dy + dz*dz)

def calculate_look_rotation(from_pos: dict, to_pos: dict) -> dict:
    """Calculate yaw/pitch to look from one position to another
    
    Returns:
        {yaw, pitch} in degrees
    """
    dx = to_pos['x'] - from_pos['x']
    dy = to_pos['y'] - from_pos['y']
    dz = to_pos['z'] - from_pos['z']
    
    # Yaw: horizontal angle
    yaw = math.degrees(math.atan2(-dx, dz))
    
    # Pitch: vertical angle
    horizontal_dist = math.sqrt(dx*dx + dz*dz)
    pitch = math.degrees(math.atan2(-dy, horizontal_dist))
    
    return {'yaw': yaw, 'pitch': pitch}
