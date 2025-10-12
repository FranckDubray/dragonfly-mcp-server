"""True Random Number Generator using physical sources.

Uses atmospheric noise (RANDOM.ORG) and quantum phenomena (Cisco QRNG)
for cryptographically secure true random numbers.

Example usage:
    # Generate random integers
    {
        "tool": "random",
        "params": {
            "operation": "generate_integers",
            "min": 1,
            "max": 100,
            "count": 5
        }
    }
    
    # Coin flip
    {
        "tool": "random",
        "params": {
            "operation": "coin_flip",
            "count": 10
        }
    }
    
    # Pick random from list
    {
        "tool": "random",
        "params": {
            "operation": "pick_random",
            "items": ["apple", "banana", "orange"],
            "count": 1
        }
    }
    
    # Quantum random bytes
    {
        "tool": "random",
        "params": {
            "operation": "generate_bytes",
            "length": 32,
            "format": "hex",
            "source": "quantum"
        }
    }

Physical sources:
    - atmospheric: RANDOM.ORG (atmospheric radio noise)
    - quantum: Cisco Outshift QRNG (quantum hardware)
    - auto: Intelligent fallback (tries quantum → atmospheric → pseudo-random)
"""
from __future__ import annotations
from typing import Dict, Any

# Import from implementation package
from ._random.api import route_operation
from ._random import spec as _spec


def run(operation: str = "generate_integers", **params) -> Dict[str, Any]:
    """Execute random operation.
    
    Args:
        operation: Operation to perform
        **params: Operation parameters
        
    Returns:
        Operation result
    """
    # Normalize operation
    op = (operation or params.get("operation") or "generate_integers").strip().lower()
    
    # Route to handler
    return route_operation(op, **params)


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec.
    
    Returns:
        OpenAI function spec
    """
    return _spec()
