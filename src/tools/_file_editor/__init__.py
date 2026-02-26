"""File Editor package — internal implementation."""
from __future__ import annotations
from typing import Dict, Any
import json
from pathlib import Path


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec.

    Returns:
        OpenAI function spec
    """
    spec_path = Path(__file__).parent.parent.parent / "tool_specs" / "file_editor.json"

    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "type": "function",
            "function": {
                "name": "file_editor",
                "displayName": "File Editor",
                "description": "S3-backed file editor with surgical editing",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": [
                                "list", "create", "edit", "append", "delete",
                                "versions", "diff", "restore", "load", "unload",
                            ],
                        }
                    },
                    "required": ["operation"],
                    "additionalProperties": False,
                },
            },
        }


__all__ = ["spec"]
