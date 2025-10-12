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
from .sources import get_random_integers, get_random_bytes


def handle_generate_integers(**params) -> Dict[str, Any]:
    """Generate random integers."""
    try:
        validated = validate_generate_integers_params(params)
        numbers = get_random_integers(
            min_val=validated["min"],
            max_val=validated["max"],
            count=validated["count"],
            unique=validated["unique"]
        )
        
        if numbers is None:
            return {"error": "Failed to generate random integers"}
        
        # MINIMAL OUTPUT
        return numbers if validated["count"] > 1 else numbers[0]
        
    except ValueError as e:
        return {"error": str(e)}


def handle_generate_floats(**params) -> Dict[str, Any]:
    """Generate random floats."""
    try:
        validated = validate_generate_floats_params(params)
        
        range_size = (validated["max"] - validated["min"]) * (10 ** validated["decimals"])
        integers = get_random_integers(
            min_val=0,
            max_val=int(range_size),
            count=validated["count"],
            unique=False
        )
        
        if integers is None:
            return {"error": "Failed to generate random floats"}
        
        scale = 10 ** validated["decimals"]
        floats = [round(validated["min"] + (i / scale), validated["decimals"]) for i in integers]
        
        # MINIMAL OUTPUT
        return floats if validated["count"] > 1 else floats[0]
        
    except ValueError as e:
        return {"error": str(e)}


def handle_generate_bytes(**params) -> Dict[str, Any]:
    """Generate random bytes."""
    try:
        validated = validate_generate_bytes_params(params)
        raw_bytes = get_random_bytes(length=validated["length"])
        
        if raw_bytes is None:
            return {"error": "Failed to generate random bytes"}
        
        # Format output
        if validated["format"] == "hex":
            return raw_bytes.hex()
        elif validated["format"] == "base64":
            import base64
            return base64.b64encode(raw_bytes).decode('ascii')
        else:  # decimal
            return list(raw_bytes)
        
    except ValueError as e:
        return {"error": str(e)}


def handle_coin_flip(**params) -> Dict[str, Any]:
    """Flip coin(s)."""
    try:
        validated = validate_coin_flip_params(params)
        numbers = get_random_integers(min_val=0, max_val=1, count=validated["count"], unique=False)
        
        if numbers is None:
            return {"error": "Failed to flip coin"}
        
        flips = ["heads" if n == 1 else "tails" for n in numbers]
        
        # MINIMAL OUTPUT
        return flips if validated["count"] > 1 else flips[0]
        
    except ValueError as e:
        return {"error": str(e)}


def handle_dice_roll(**params) -> Dict[str, Any]:
    """Roll dice."""
    try:
        validated = validate_dice_roll_params(params)
        numbers = get_random_integers(
            min_val=1,
            max_val=validated["sides"],
            count=validated["count"],
            unique=False
        )
        
        if numbers is None:
            return {"error": "Failed to roll dice"}
        
        # MINIMAL OUTPUT
        return numbers if validated["count"] > 1 else numbers[0]
        
    except ValueError as e:
        return {"error": str(e)}


def handle_shuffle(**params) -> Dict[str, Any]:
    """Shuffle a list."""
    try:
        validated = validate_shuffle_params(params)
        items = validated["items"]
        count = len(items)
        
        indices = get_random_integers(min_val=0, max_val=count - 1, count=count * 2, unique=False)
        
        if indices is None:
            return {"error": "Failed to shuffle"}
        
        # Fisher-Yates shuffle
        shuffled = items.copy()
        idx = 0
        for i in range(count - 1, 0, -1):
            j = indices[idx] % (i + 1)
            shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
            idx += 1
        
        # MINIMAL OUTPUT
        return shuffled
        
    except ValueError as e:
        return {"error": str(e)}


def handle_pick_random(**params) -> Dict[str, Any]:
    """Pick random item(s) from list."""
    try:
        validated = validate_pick_random_params(params)
        items = validated["items"]
        count = validated["count"]
        
        indices = get_random_integers(min_val=0, max_val=len(items) - 1, count=count, unique=True)
        
        if indices is None:
            return {"error": "Failed to pick random"}
        
        picked = [items[i] for i in indices]
        
        # MINIMAL OUTPUT
        return picked if count > 1 else picked[0]
        
    except ValueError as e:
        return {"error": str(e)}
