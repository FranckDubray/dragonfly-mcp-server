"""
Portal Model Access — Manage model visibility per tenant & company.

Administers which AI models are visible for each tenant and company
on the AI You portal. Supports inheritance (tenant→company) and
fine-grained per-model / per-editor toggles.

Example - Overview:
  {"tool": "portal_model_access", "params": {"operation": "overview"}}

Example - Tenant models:
  {"tool": "portal_model_access", "params": {
    "operation": "tenant_models", "tenant_id": 1
  }}

Example - Toggle model for tenant:
  {"tool": "portal_model_access", "params": {
    "operation": "set_tenant_model",
    "tenant_id": 1, "model_id": 125, "active": false
  }}
"""
from __future__ import annotations
from typing import Dict, Any

from ._portal_model_access.api import route_operation
from ._portal_model_access import spec as _spec


def run(**params) -> Dict[str, Any]:
    """Execute portal model access operation."""
    operation = params.get("operation")
    if not operation:
        return {"error": "Parameter 'operation' is required"}
    operation = str(operation).strip().lower()
    clean = {k: v for k, v in params.items() if k != "operation"}
    return route_operation(operation, **clean)


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec."""
    return _spec()
