"""Core logic for random number generation."""

from typing import Dict, Any, List
import random as stdlib_random
from .validators import (
    validate_generate_integers_params,
    validate_generate_floats_params,
    validate_generate_bytes_params,
    validate_coin_flip_params,
    validate_dice_roll_params,
    validate_shuffle_params,
    validate_pick_random_params
)
from .sources import get_random_integers, get_random_bytes, RandomSource


def handle_generate_integers(**params) -> Dict[str, Any]:
    """Generate random integers.
    
    Args:
        **params: Parameters (min, max, count, unique, source)
        
    Returns:
        Random integers
    """
    try:
        validated = validate_generate_integers_params(params)
        
        # Get random integers from physical source
        numbers = get_random_integers(
            min_val=validated["min"],
            max_val=validated["max"],
            count=validated["count"],
            unique=validated["unique"],
            source=validated["source"]
        )
        
        if numbers is None:
            return {
                "error": "Failed to generate random integers from all sources",
                "note": "All physical sources failed. Check API keys and connectivity."
            }
        
        return {
            "success": True,
            "operation": "generate_integers",
            "numbers": numbers,
            "count": len(numbers),
            "min": validated["min"],
            "max": validated["max"],
            "unique": validated["unique"],
            "source_used": numbers.source if hasattr(numbers, 'source') else "unknown"
        }
        
    except ValueError as e:
        return {"error": f"Validation error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def handle_generate_floats(**params) -> Dict[str, Any]:
    """Generate random floats.
    
    Args:
        **params: Parameters (min, max, count, decimals, source)
        
    Returns:
        Random floats
    """
    try:
        validated = validate_generate_floats_params(params)
        
        # Generate integers then convert to floats with decimals
        range_size = (validated["max"] - validated["min"]) * (10 ** validated["decimals"])
        integers = get_random_integers(
            min_val=0,
            max_val=int(range_size),
            count=validated["count"],
            unique=False,
            source=validated["source"]
        )
        
        if integers is None:
            return {
                "error": "Failed to generate random floats from all sources",
                "note": "All physical sources failed. Check API keys and connectivity."
            }
        
        # Convert to floats
        scale = 10 ** validated["decimals"]
        floats = [round(validated["min"] + (i / scale), validated["decimals"]) for i in integers]
        
        return {
            "success": True,
            "operation": "generate_floats",
            "numbers": floats,
            "count": len(floats),
            "min": validated["min"],
            "max": validated["max"],
            "decimals": validated["decimals"],
            "source_used": integers.source if hasattr(integers, 'source') else "unknown"
        }
        
    except ValueError as e:
        return {"error": f"Validation error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def handle_generate_bytes(**params) -> Dict[str, Any]:
    """Generate random bytes.
    
    Args:
        **params: Parameters (length, format, source)
        
    Returns:
        Random bytes in specified format
    """
    try:
        validated = validate_generate_bytes_params(params)
        
        # Get random bytes from physical source
        raw_bytes = get_random_bytes(
            length=validated["length"],
            source=validated["source"]
        )
        
        if raw_bytes is None:
            return {
                "error": "Failed to generate random bytes from all sources",
                "note": "All physical sources failed. Check API keys and connectivity."
            }
        
        # Format output
        if validated["format"] == "hex":
            output = raw_bytes.hex()
        elif validated["format"] == "base64":
            import base64
            output = base64.b64encode(raw_bytes).decode('ascii')
        else:  # decimal
            output = list(raw_bytes)
        
        return {
            "success": True,
            "operation": "generate_bytes",
            "bytes": output,
            "length": validated["length"],
            "format": validated["format"],
            "source_used": raw_bytes.source if hasattr(raw_bytes, 'source') else "unknown"
        }
        
    except ValueError as e:
        return {"error": f"Validation error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def handle_coin_flip(**params) -> Dict[str, Any]:
    """Flip coin(s).
    
    Args:
        **params: Parameters (count, source)
        
    Returns:
        Coin flip results (heads/tails)
    """
    try:
        validated = validate_coin_flip_params(params)
        
        # Generate random bits (0 or 1)
        numbers = get_random_integers(
            min_val=0,
            max_val=1,
            count=validated["count"],
            unique=False,
            source=validated["source"]
        )
        
        if numbers is None:
            return {
                "error": "Failed to flip coin from all sources",
                "note": "All physical sources failed. Check API keys and connectivity."
            }
        
        # Convert to heads/tails
        flips = ["heads" if n == 1 else "tails" for n in numbers]
        
        return {
            "success": True,
            "operation": "coin_flip",
            "flips": flips,
            "count": len(flips),
            "heads": flips.count("heads"),
            "tails": flips.count("tails"),
            "source_used": numbers.source if hasattr(numbers, 'source') else "unknown"
        }
        
    except ValueError as e:
        return {"error": f"Validation error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def handle_dice_roll(**params) -> Dict[str, Any]:
    """Roll dice.
    
    Args:
        **params: Parameters (sides, count, source)
        
    Returns:
        Dice roll results
    """
    try:
        validated = validate_dice_roll_params(params)
        
        # Generate random numbers (1 to sides)
        numbers = get_random_integers(
            min_val=1,
            max_val=validated["sides"],
            count=validated["count"],
            unique=False,
            source=validated["source"]
        )
        
        if numbers is None:
            return {
                "error": "Failed to roll dice from all sources",
                "note": "All physical sources failed. Check API keys and connectivity."
            }
        
        return {
            "success": True,
            "operation": "dice_roll",
            "rolls": numbers,
            "count": len(numbers),
            "sides": validated["sides"],
            "sum": sum(numbers),
            "source_used": numbers.source if hasattr(numbers, 'source') else "unknown"
        }
        
    except ValueError as e:
        return {"error": f"Validation error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def handle_shuffle(**params) -> Dict[str, Any]:
    """Shuffle a list.
    
    Args:
        **params: Parameters (items, source)
        
    Returns:
        Shuffled list
    """
    try:
        validated = validate_shuffle_params(params)
        items = validated["items"]
        
        # Generate random permutation indices
        count = len(items)
        indices = get_random_integers(
            min_val=0,
            max_val=count - 1,
            count=count * 2,  # Generate extra for Fisher-Yates
            unique=False,
            source=validated["source"]
        )
        
        if indices is None:
            return {
                "error": "Failed to shuffle from all sources",
                "note": "All physical sources failed. Check API keys and connectivity."
            }
        
        # Fisher-Yates shuffle with true random indices
        shuffled = items.copy()
        idx = 0
        for i in range(count - 1, 0, -1):
            j = indices[idx] % (i + 1)
            shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
            idx += 1
        
        return {
            "success": True,
            "operation": "shuffle",
            "shuffled": shuffled,
            "original_count": count,
            "source_used": indices.source if hasattr(indices, 'source') else "unknown"
        }
        
    except ValueError as e:
        return {"error": f"Validation error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def handle_pick_random(**params) -> Dict[str, Any]:
    """Pick random item(s) from list.
    
    Args:
        **params: Parameters (items, count, source)
        
    Returns:
        Random picked items
    """
    try:
        validated = validate_pick_random_params(params)
        items = validated["items"]
        count = validated["count"]
        
        # Generate random indices
        indices = get_random_integers(
            min_val=0,
            max_val=len(items) - 1,
            count=count,
            unique=True,  # No duplicates
            source=validated["source"]
        )
        
        if indices is None:
            return {
                "error": "Failed to pick random from all sources",
                "note": "All physical sources failed. Check API keys and connectivity."
            }
        
        # Pick items
        picked = [items[i] for i in indices]
        
        return {
            "success": True,
            "operation": "pick_random",
            "picked": picked,
            "count": len(picked),
            "total_items": len(items),
            "source_used": indices.source if hasattr(indices, 'source') else "unknown"
        }
        
    except ValueError as e:
        return {"error": f"Validation error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
