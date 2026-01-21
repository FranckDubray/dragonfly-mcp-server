"""Légifrance LEGI package - internal implementation."""
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
    spec_path = Path(__file__).parent.parent.parent / "tool_specs" / "legifrance_legi.json"
    
    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback minimal spec (should not happen in production)
        return {
            "type": "function",
            "function": {
                "name": "legifrance_legi",
                "displayName": "Légifrance LEGI",
                "description": "Accès aux codes juridiques français (corpus LEGI)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {"type": "string", "enum": ["get_summary", "get_article"]}
                    },
                    "required": ["operation"],
                    "additionalProperties": False
                }
            }
        }


# Export spec for bootstrap file
__all__ = ["spec"]
