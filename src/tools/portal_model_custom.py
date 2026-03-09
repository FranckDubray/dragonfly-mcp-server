"""
Portal Custom Model Manager — Create and manage custom models.

A custom model wraps an existing model with injected tools and preprompt,
hidden from the user. The underlying model is hardcoded in the input field.

Example - Preview:
  {"tool": "portal_model_custom", "params": {
    "operation": "preview",
    "source_model_id": 134,
    "name": "gpt-dgy",
    "display_name": "GPT DGY"
  }}

Example - Create:
  {"tool": "portal_model_custom", "params": {
    "operation": "create",
    "source_model_id": 134,
    "name": "gpt-dgy",
    "display_name": "GPT DGY"
  }}

Example - Add tools:
  {"tool": "portal_model_custom", "params": {
    "operation": "add_tools",
    "model_id": 157,
    "tool_ids": [6, 153, 168]
  }}
"""
from __future__ import annotations
from typing import Dict, Any

from ._portal_model_custom.api import route_operation
from ._portal_model_custom import spec as _spec


def run(**params) -> Dict[str, Any]:
    """Execute custom model operation."""
    operation = params.get("operation")
    if not operation:
        return {"error": "Parameter 'operation' is required"}

    operation = str(operation).strip().lower()
    clean = {k: v for k, v in params.items() if k != "operation"}

    return route_operation(operation, **clean)


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec."""
    return _spec()
