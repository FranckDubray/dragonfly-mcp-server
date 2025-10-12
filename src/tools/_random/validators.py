"""Input validation for random operations."""

from typing import Dict, Any


def validate_generate_integers_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate generate_integers parameters."""
    min_val = params.get("min", 0)
    max_val = params.get("max", 100)
    count = params.get("count", 1)
    unique = params.get("unique", False)
    
    if not isinstance(min_val, int):
        raise ValueError("Parameter 'min' must be an integer")
    if not isinstance(max_val, int):
        raise ValueError("Parameter 'max' must be an integer")
    if min_val >= max_val:
        raise ValueError("Parameter 'min' must be less than 'max'")
    
    if not isinstance(count, int) or count < 1 or count > 10000:
        raise ValueError("Parameter 'count' must be between 1 and 10000")
    
    if unique and count > (max_val - min_val + 1):
        raise ValueError(f"Cannot generate {count} unique numbers in range [{min_val}, {max_val}]")
    
    return {"min": min_val, "max": max_val, "count": count, "unique": unique}


def validate_generate_floats_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate generate_floats parameters."""
    min_val = params.get("min", 0)
    max_val = params.get("max", 1)
    count = params.get("count", 1)
    decimals = params.get("decimals", 2)
    
    if not isinstance(min_val, (int, float)):
        raise ValueError("Parameter 'min' must be a number")
    if not isinstance(max_val, (int, float)):
        raise ValueError("Parameter 'max' must be a number")
    if min_val >= max_val:
        raise ValueError("Parameter 'min' must be less than 'max'")
    
    if not isinstance(count, int) or count < 1 or count > 10000:
        raise ValueError("Parameter 'count' must be between 1 and 10000")
    
    if not isinstance(decimals, int) or decimals < 1 or decimals > 20:
        raise ValueError("Parameter 'decimals' must be between 1 and 20")
    
    return {"min": min_val, "max": max_val, "count": count, "decimals": decimals}


def validate_generate_bytes_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate generate_bytes parameters."""
    length = params.get("length", 16)
    format_type = params.get("format", "hex")
    
    if not isinstance(length, int) or length < 1 or length > 1000:
        raise ValueError("Parameter 'length' must be between 1 and 1000")
    
    if format_type not in ["hex", "base64", "decimal"]:
        raise ValueError("Parameter 'format' must be 'hex', 'base64', or 'decimal'")
    
    return {"length": length, "format": format_type}


def validate_coin_flip_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate coin_flip parameters."""
    count = params.get("count", 1)
    
    if not isinstance(count, int) or count < 1 or count > 10000:
        raise ValueError("Parameter 'count' must be between 1 and 10000")
    
    return {"count": count}


def validate_dice_roll_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate dice_roll parameters."""
    sides = params.get("sides", 6)
    count = params.get("count", 1)
    
    if not isinstance(sides, int) or sides < 3 or sides > 100:
        raise ValueError("Parameter 'sides' must be between 3 and 100")
    
    if not isinstance(count, int) or count < 1 or count > 10000:
        raise ValueError("Parameter 'count' must be between 1 and 10000")
    
    return {"sides": sides, "count": count}


def validate_shuffle_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate shuffle parameters."""
    items = params.get("items")
    
    if not isinstance(items, list):
        raise ValueError("Parameter 'items' must be a list")
    
    if len(items) < 1:
        raise ValueError("Parameter 'items' must contain at least 1 item")
    
    if len(items) > 10000:
        raise ValueError("Parameter 'items' cannot contain more than 10000 items")
    
    return {"items": items}


def validate_pick_random_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate pick_random parameters."""
    items = params.get("items")
    count = params.get("count", 1)
    
    if not isinstance(items, list):
        raise ValueError("Parameter 'items' must be a list")
    
    if len(items) < 1:
        raise ValueError("Parameter 'items' must contain at least 1 item")
    
    if len(items) > 10000:
        raise ValueError("Parameter 'items' cannot contain more than 10000 items")
    
    if not isinstance(count, int) or count < 1:
        raise ValueError("Parameter 'count' must be at least 1")
    
    if count > len(items):
        raise ValueError(f"Cannot pick {count} items from a list of {len(items)} items")
    
    return {"items": items, "count": count}
