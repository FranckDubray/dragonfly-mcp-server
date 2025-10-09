"""Ship Tracker tool initialization."""

from pathlib import Path
import json


def spec():
    """Load canonical JSON spec for ship_tracker tool.
    
    Returns:
        dict: OpenAI function specification
    """
    spec_path = Path(__file__).resolve().parent.parent.parent / "tool_specs" / "ship_tracker.json"
    
    if spec_path.exists():
        with open(spec_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Fallback spec if JSON not found
    return {
        "type": "function",
        "function": {
            "name": "ship_tracker",
            "displayName": "Ship Tracker",
            "description": "Track ships and vessels in real-time using AIS data via aisstream.io API. Free, no authentication required. Get vessel positions, speed, heading, destination, and more.",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["track_ships", "get_ship_details", "get_port_traffic"],
                        "description": "Operation to perform"
                    }
                },
                "required": ["operation"],
                "additionalProperties": False
            }
        }
    }
