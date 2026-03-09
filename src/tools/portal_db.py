"""
Portal DB — Read-only access to AI You portal MySQL database.

Queries the production database (appwebldragonfly) via SSH tunnel
through the bastion. Supports SELECT, SHOW, DESCRIBE, EXPLAIN only.

Example - Count users:
  {"tool": "portal_db", "params": {"operation": "count", "table": "user"}}

Example - Query with pagination:
  {"tool": "portal_db", "params": {
    "operation": "query",
    "sql": "SELECT id, email, first_name FROM user ORDER BY id",
    "limit": 50, "offset": 0
  }}

Example - Describe table:
  {"tool": "portal_db", "params": {"operation": "describe", "table": "thread_history"}}
"""
from __future__ import annotations
from typing import Dict, Any

from ._portal_db.api import route_operation
from ._portal_db import spec as _spec


def run(**params) -> Dict[str, Any]:
    """Execute portal_db operation.

    Args:
        **params: Operation parameters (operation, sql, table, etc.)

    Returns:
        Query results or error
    """
    operation = params.get("operation")
    if not operation:
        return {"error": "Parameter 'operation' is required"}

    operation = str(operation).strip().lower()
    clean_params = {k: v for k, v in params.items() if k != "operation"}

    return route_operation(operation, **clean_params)


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec."""
    return _spec()
