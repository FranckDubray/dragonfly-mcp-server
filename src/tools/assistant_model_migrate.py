"""
Assistant Model Migration — Migrate assistants from one AI model to another.

Supports dry-run preview, batch migration, rollback, and history.
All operations are logged in a local SQLite database for traceability.

Example - List models:
  {"tool": "assistant_model_migrate", "params": {"operation": "models"}}

Example - Preview migration:
  {"tool": "assistant_model_migrate", "params": {
    "operation": "preview", "from_model_id": 1, "to_model_id": 73
  }}

Example - Execute migration:
  {"tool": "assistant_model_migrate", "params": {
    "operation": "execute", "from_model_id": 1, "to_model_id": 73
  }}

Example - Rollback:
  {"tool": "assistant_model_migrate", "params": {
    "operation": "rollback", "migration_id": "mig_20260304_143022"
  }}
"""
from __future__ import annotations
from typing import Dict, Any

from ._assistant_model_migrate.api import route_operation
from ._assistant_model_migrate import spec as _spec


def run(**params) -> Dict[str, Any]:
    """Execute migration operation."""
    operation = params.get("operation")
    if not operation:
        return {"error": "Parameter 'operation' is required"}

    operation = str(operation).strip().lower()
    clean = {k: v for k, v in params.items() if k != "operation"}

    return route_operation(operation, **clean)


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec."""
    return _spec()
