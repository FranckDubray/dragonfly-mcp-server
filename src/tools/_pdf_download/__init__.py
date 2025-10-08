"""PDF Download tool package - internal implementation.

This package contains the implementation modules.
The public interface is exposed via src/tools/pdf_download.py (bootstrap file).
"""
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
    spec_path = Path(__file__).parent.parent.parent / "tool_specs" / "pdf_download.json"
    
    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback minimal spec (should not happen in production)
        return {
            "type": "function",
            "function": {
                "name": "pdf_download",
                "displayName": "PDF Download",
                "description": "Download PDF files from URLs to docs/pdfs",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {"type": "string", "enum": ["download"]},
                        "url": {"type": "string"},
                        "filename": {"type": "string"},
                        "overwrite": {"type": "boolean", "default": False},
                        "timeout": {"type": "integer", "default": 60}
                    },
                    "required": ["operation", "url"],
                    "additionalProperties": False
                }
            }
        }


# Export spec for bootstrap file
__all__ = ["spec"]
