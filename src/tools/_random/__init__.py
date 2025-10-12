"""True Random Number Generator tool initialization."""

from pathlib import Path
import json


def spec():
    """Load canonical JSON spec for random tool.
    
    Returns:
        dict: OpenAI function specification
    """
    spec_path = Path(__file__).resolve().parent.parent.parent / "tool_specs" / "random.json"
    
    if spec_path.exists():
        with open(spec_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Fallback spec if JSON not found
    return {
        "type": "function",
        "function": {
            "name": "random",
            "displayName": "True Random Numbers",
            "description": "Generate true random numbers using physical sources (atmospheric noise, quantum phenomena).",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["generate_integers", "generate_floats", "generate_bytes", "coin_flip", "dice_roll", "shuffle", "pick_random"],
                        "description": "Operation to perform"
                    }
                },
                "required": ["operation"],
                "additionalProperties": False
            }
        }
    }
