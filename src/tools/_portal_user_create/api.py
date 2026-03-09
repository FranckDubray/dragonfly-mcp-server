"""API routing for portal user creation."""
from __future__ import annotations
from typing import Dict, Any

from .core import list_companies, preview, execute


def route_operation(operation: str, **params) -> Dict[str, Any]:
    """Route operation to handler."""
    try:
        if operation == "list_companies":
            return list_companies(
                limit=params.get("limit", 50),
                offset=params.get("offset", 0),
            )

        elif operation == "preview":
            company_id = params.get("company_id")
            users = params.get("users")
            if not company_id:
                return {"error": "company_id is required"}
            if not users or not isinstance(users, list):
                return {"error": "users array is required"}
            return preview(company_id=company_id, users_input=users)

        elif operation == "execute":
            company_id = params.get("company_id")
            users = params.get("users")
            if not company_id:
                return {"error": "company_id is required"}
            if not users or not isinstance(users, list):
                return {"error": "users array is required"}
            return execute(company_id=company_id, users_input=users)

        else:
            return {"error": f"Unknown operation: {operation}"}

    except Exception as e:
        return {"error": f"Operation failed: {str(e)}", "error_type": "unknown"}
