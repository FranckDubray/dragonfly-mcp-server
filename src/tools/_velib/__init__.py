"""Vélib' Métropole package - internal implementation."""
from __future__ import annotations
from typing import Dict, Any
import json
from pathlib import Path


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec.
    
    Returns:
        OpenAI function spec
    """
    # Load from canonical JSON file
    spec_path = Path(__file__).parent.parent.parent / "tool_specs" / "velib.json"
    
    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback minimal spec (should not happen in production)
        return {
            "type": "function",
            "function": {
                "name": "velib",
                "displayName": "Vélib' Métropole",
                "description": "Gestionnaire de cache Vélib' Métropole",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {"type": "string", "enum": ["refresh_stations", "get_availability", "check_cache"]},
                        "station_code": {"type": "string"}
                    },
                    "required": ["operation"],
                    "additionalProperties": False
                }
            }
        }


# Export spec for bootstrap file
__all__ = ["spec"]
