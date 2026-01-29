"""SSH Client package - internal implementation."""
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
    spec_path = Path(__file__).parent.parent.parent / "tool_specs" / "ssh_client.json"
    
    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback minimal spec (should not happen in production)
        return {
            "type": "function",
            "function": {
                "name": "ssh_client",
                "displayName": "SSH Client",
                "description": "Universal SSH/SFTP client",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["exec", "upload", "download", "status"]
                        },
                        "host": {"type": "string"},
                        "username": {"type": "string"},
                        "auth_type": {
                            "type": "string",
                            "enum": ["password", "key", "agent"]
                        }
                    },
                    "required": ["operation", "host", "username", "auth_type"],
                    "additionalProperties": False
                }
            }
        }


# Export spec for bootstrap file
__all__ = ["spec"]
