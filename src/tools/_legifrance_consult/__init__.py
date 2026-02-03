"""Légifrance Consult package - internal implementation."""
from __future__ import annotations
from typing import Dict, Any
import json
from pathlib import Path


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec."""
    spec_path = Path(__file__).parent.parent.parent / "tool_specs" / "legifrance_consult.json"
    
    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback minimal spec
        return {
            "type": "function",
            "function": {
                "name": "legifrance_consult",
                "description": "Consultation corpus juridique français",
                "parameters": {"type": "object", "properties": {}}
            }
        }

__all__ = ["spec"]
