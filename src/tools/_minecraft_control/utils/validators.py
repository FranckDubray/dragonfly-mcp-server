"""
Parameter validation
"""
import logging
from ..config import VALIDATION_LIMITS, WORLD_Y_MIN, WORLD_Y_MAX, WORLD_XZ_LIMIT

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Parameter validation error"""
    pass

def validate_params(operation: str, params: dict) -> dict:
    """Validate operation parameters
    
    Args:
        operation: Operation name
        params: Parameters dict
        
    Returns:
        Validated/normalized params dict
        
    Raises:
        ValidationError: Invalid params
    """
    validators = {
        "spawn_entities": _validate_spawn_entities,
        "build_structure": _validate_build_structure,
        "import_3d_model": _validate_import_model,
        "control_player": _validate_control_player,
        "set_environment": _validate_set_environment,
        "batch_commands": _validate_batch_commands
    }
    
    validator = validators.get(operation)
    if validator:
        return validator(params)
    
    return params

def _validate_spawn_entities(params: dict) -> dict:
    """Validate spawn_entities params"""
    if 'entity_type' not in params:
        raise ValidationError("entity_type required")
    
    count = params.get('count', 1)
    limits = VALIDATION_LIMITS['entity_count']
    if not limits['min'] <= count <= limits['max']:
        raise ValidationError(f"count must be {limits['min']}-{limits['max']}")
    
    if 'position' in params and params['position']:
        _validate_position(params['position'])
    
    if 'offset' in params:
        _validate_offset(params['offset'])
    
    return params

def _validate_build_structure(params: dict) -> dict:
    """Validate build_structure params"""
    if 'block_type' not in params:
        raise ValidationError("block_type required")
    
    if 'dimensions' in params:
        dims = params['dimensions']
        for key in ['width', 'height', 'depth']:
            if key in dims:
                limits = VALIDATION_LIMITS['dimensions'][key]
                val = dims[key]
                if not limits['min'] <= val <= limits['max']:
                    raise ValidationError(f"{key} must be {limits['min']}-{limits['max']}")
    
    if 'start_pos' in params and params['start_pos']:
        _validate_position(params['start_pos'])
    
    if 'end_pos' in params and params['end_pos']:
        _validate_position(params['end_pos'])
    
    return params

def _validate_import_model(params: dict) -> dict:
    """Validate import_3d_model params"""
    if 'model_path' not in params:
        raise ValidationError("model_path required")
    
    scale = params.get('scale', 1.0)
    limits = VALIDATION_LIMITS['scale']
    if not limits['min'] <= scale <= limits['max']:
        raise ValidationError(f"scale must be {limits['min']}-{limits['max']}")
    
    voxel_res = params.get('voxel_resolution', 1.0)
    limits = VALIDATION_LIMITS['voxel_resolution']
    if not limits['min'] <= voxel_res <= limits['max']:
        raise ValidationError(f"voxel_resolution must be {limits['min']}-{limits['max']}")
    
    return params

def _validate_control_player(params: dict) -> dict:
    """Validate control_player params"""
    if 'player_action' not in params:
        raise ValidationError("player_action required")
    
    if 'yaw' in params:
        limits = VALIDATION_LIMITS['yaw']
        yaw = params['yaw']
        if not limits['min'] <= yaw <= limits['max']:
            raise ValidationError(f"yaw must be {limits['min']}-{limits['max']}")
    
    if 'pitch' in params:
        limits = VALIDATION_LIMITS['pitch']
        pitch = params['pitch']
        if not limits['min'] <= pitch <= limits['max']:
            raise ValidationError(f"pitch must be {limits['min']}-{limits['max']}")
    
    if 'target_position' in params and params['target_position']:
        _validate_position(params['target_position'])
    
    return params

def _validate_set_environment(params: dict) -> dict:
    """Validate set_environment params"""
    if 'time_value' in params:
        limits = VALIDATION_LIMITS['time_value']
        val = params['time_value']
        if not limits['min'] <= val <= limits['max']:
            raise ValidationError(f"time_value must be {limits['min']}-{limits['max']}")
    
    return params

def _validate_batch_commands(params: dict) -> dict:
    """Validate batch_commands params"""
    if 'commands' not in params:
        raise ValidationError("commands array required")
    
    if not isinstance(params['commands'], list):
        raise ValidationError("commands must be array")
    
    if len(params['commands']) == 0:
        raise ValidationError("commands array cannot be empty")
    
    delay = params.get('delay_ms', 50)
    limits = VALIDATION_LIMITS['delay_ms']
    if not limits['min'] <= delay <= limits['max']:
        raise ValidationError(f"delay_ms must be {limits['min']}-{limits['max']}")
    
    return params

def _validate_position(pos: dict):
    """Validate world coordinates"""
    if 'x' in pos and abs(pos['x']) > WORLD_XZ_LIMIT:
        raise ValidationError(f"x coordinate out of world bounds (±{WORLD_XZ_LIMIT})")
    
    if 'z' in pos and abs(pos['z']) > WORLD_XZ_LIMIT:
        raise ValidationError(f"z coordinate out of world bounds (±{WORLD_XZ_LIMIT})")
    
    if 'y' in pos:
        y = pos['y']
        if not WORLD_Y_MIN <= y <= WORLD_Y_MAX:
            raise ValidationError(f"y must be {WORLD_Y_MIN}-{WORLD_Y_MAX}")

def _validate_offset(offset: dict):
    """Validate offset values"""
    for key in ['forward', 'up', 'right']:
        if key in offset and abs(offset[key]) > 1000:
            raise ValidationError(f"offset.{key} too large (max ±1000)")
