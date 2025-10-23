"""
Parameter validation
"""
import logging
import re
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
        "batch_commands": _validate_batch_commands,
        "list_entities": _validate_list_entities,
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

# ---- New: list_entities validator ----

def _validate_list_entities(params: dict) -> dict:
    """Validate list_entities params."""
    # selector
    if 'selector' in params and params['selector'] is not None and not isinstance(params['selector'], str):
        raise ValidationError("selector must be string")

    # limit
    limit = params.get('limit', 64)
    if not isinstance(limit, int):
        try:
            limit = int(limit)
        except Exception:
            raise ValidationError("limit must be integer")
    if not (1 <= limit <= 500):
        raise ValidationError("limit must be between 1 and 500")
    params['limit'] = limit

    # sort_by
    if 'sort_by' in params and params['sort_by'] is not None:
        sort_by = str(params['sort_by']).lower()
        if sort_by not in ("distance", "y", "type", "name"):
            raise ValidationError("sort_by must be one of: distance, y, type, name")
        params['sort_by'] = sort_by

    # descending
    if 'descending' in params and params['descending'] is not None and not isinstance(params['descending'], bool):
        raise ValidationError("descending must be boolean")

    # pos_ref
    pos_ref = str(params.get('pos_ref', 'feet')).lower()
    if pos_ref not in ("feet", "eyes"):
        raise ValidationError("pos_ref must be 'feet' or 'eyes'")
    params['pos_ref'] = pos_ref

    # include flags
    for key in ('include_passengers', 'include_riding'):
        if key in params and params[key] is not None and not isinstance(params[key], bool):
            raise ValidationError(f"{key} must be boolean")

    # filters
    flt = params.get('filters')
    if flt is not None and not isinstance(flt, dict):
        raise ValidationError("filters must be object")
    if isinstance(flt, dict):
        for arr_key in ('types', 'tags_all', 'tags_any', 'tags_none'):
            if arr_key in flt and flt[arr_key] is not None:
                if not isinstance(flt[arr_key], list) or not all(isinstance(x, str) for x in flt[arr_key]):
                    raise ValidationError(f"filters.{arr_key} must be array of strings")
        if 'name' in flt and flt['name'] is not None and not isinstance(flt['name'], str):
            raise ValidationError("filters.name must be string")
        if 'custom_name_pattern' in flt and flt['custom_name_pattern'] is not None:
            pat = flt['custom_name_pattern']
            if not isinstance(pat, str):
                raise ValidationError("filters.custom_name_pattern must be string")
            # Validate regex pattern
            try:
                re.compile(pat)
            except Exception as e:
                raise ValidationError(f"filters.custom_name_pattern invalid regex: {e}")

    # area
    area = params.get('area')
    if area is not None and not isinstance(area, dict):
        raise ValidationError("area must be object")
    if isinstance(area, dict):
        mode = str(area.get('mode', 'sphere')).lower()
        if mode not in ("sphere", "aabb"):
            raise ValidationError("area.mode must be 'sphere' or 'aabb'")
        area['mode'] = mode
        if 'center' in area and area['center'] is not None:
            _validate_position(area['center'])
        if mode == 'sphere':
            if 'radius' in area and area['radius'] is not None:
                try:
                    r = float(area['radius'])
                except Exception:
                    raise ValidationError("area.radius must be number")
                if r < 0:
                    raise ValidationError("area.radius must be >= 0")
        else:  # aabb
            aabb = area.get('aabb')
            if aabb is None or not isinstance(aabb, dict):
                raise ValidationError("area.aabb must be object for mode='aabb'")
            for corner in ('min', 'max'):
                if corner not in aabb or not isinstance(aabb[corner], dict):
                    raise ValidationError(f"area.aabb.{corner} must be object")
                _validate_position(aabb[corner])

    # fields
    if 'fields' in params and params['fields'] is not None:
        fields = params['fields']
        if not isinstance(fields, list) or not all(isinstance(x, str) for x in fields):
            raise ValidationError("fields must be array of strings")
        allowed = {"uuid","name","custom_name","type","pos","yaw","pitch","tags","dimension","nbt_min"}
        for f in fields:
            if f not in allowed:
                raise ValidationError(f"fields contains invalid value: {f}")

    # relative_to_player / offset
    if 'relative_to_player' in params and params['relative_to_player'] is not None and not isinstance(params['relative_to_player'], bool):
        raise ValidationError("relative_to_player must be boolean")
    if 'offset' in params and params['offset'] is not None:
        _validate_offset(params['offset'])

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
