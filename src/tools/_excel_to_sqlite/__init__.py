"""
Excel to SQLite converter package.
Imports Excel data into SQLite databases with automatic schema detection.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

_SPEC_DIR = Path(__file__).resolve().parent.parent.parent / "tool_specs"


def spec() -> Dict[str, Any]:
    """Load and return the tool specification."""
    spec_path = _SPEC_DIR / "excel_to_sqlite.json"
    if spec_path.is_file():
        with open(spec_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Fallback minimal spec
    return {
        "type": "function",
        "function": {
            "name": "excel_to_sqlite",
            "displayName": "Excel to SQLite",
            "description": "Import Excel data into SQLite database",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["import_excel", "preview", "get_sheets", "validate_mapping", "get_info"]
                    }
                },
                "required": ["operation"]
            }
        }
    }


__all__ = ["spec"]
