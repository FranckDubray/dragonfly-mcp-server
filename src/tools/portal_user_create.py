"""
Portal User Create — Batch create users on the AI You portal.

Creates users with ROLE_USER only (never admin). Detects first/last name
from email if not provided. Generates secure passwords.

Example - List companies:
  {"tool": "portal_user_create", "params": {"operation": "list_companies"}}

Example - Preview:
  {"tool": "portal_user_create", "params": {
    "operation": "preview",
    "company_id": 86,
    "users": [
      {"email": "lydia.bouquet@partedis.com"},
      {"email": "david.fillon@partedis.com", "first_name": "David", "last_name": "Fillon"}
    ]
  }}

Example - Execute:
  {"tool": "portal_user_create", "params": {
    "operation": "execute",
    "company_id": 86,
    "users": [{"email": "lydia.bouquet@partedis.com"}]
  }}
"""
from __future__ import annotations
from typing import Dict, Any

from ._portal_user_create.api import route_operation
from ._portal_user_create import spec as _spec


def run(**params) -> Dict[str, Any]:
    """Execute portal user creation operation."""
    operation = params.get("operation")
    if not operation:
        return {"error": "Parameter 'operation' is required"}

    operation = str(operation).strip().lower()
    clean = {k: v for k, v in params.items() if k != "operation"}

    return route_operation(operation, **clean)


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec."""
    return _spec()
