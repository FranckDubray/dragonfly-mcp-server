"""Flight Tracker package - internal implementation."""
from __future__ import annotations
from typing import Dict, Any
import json
from pathlib import Path


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec.
    
    Returns:
        OpenAI function spec
    """
    spec_path = Path(__file__).parent.parent.parent / "tool_specs" / "flight_tracker.json"
    
    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback minimal spec
        return {
            "type": "function",
            "function": {
                "name": "flight_tracker",
                "displayName": "Flight Tracker",
                "description": "Track aircraft in real-time",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {"type": "string", "enum": ["track_flights"]},
                        "latitude": {"type": "number"},
                        "longitude": {"type": "number"},
                        "radius_km": {"type": "number"}
                    },
                    "required": ["operation", "latitude", "longitude", "radius_km"],
                    "additionalProperties": False
                }
            }
        }


__all__ = ["spec"]
