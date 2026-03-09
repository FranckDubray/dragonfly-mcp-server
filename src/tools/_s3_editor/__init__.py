"""S3 Editor package — thin alias over _file_editor.

All logic lives in _file_editor. This package only overrides spec()
to point to the s3_editor.json canonical spec.
"""
from __future__ import annotations
from typing import Dict, Any
import json
from pathlib import Path


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec for s3_editor.

    Returns:
        OpenAI function spec
    """
    spec_path = Path(__file__).parent.parent.parent / "tool_specs" / "s3_editor.json"

    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "type": "function",
            "function": {
                "name": "s3_editor",
                "displayName": "S3 Editor",
                "description": "S3-backed file editor with surgical editing (alias of file_editor)",
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
