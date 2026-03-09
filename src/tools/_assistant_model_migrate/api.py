"""API routing for assistant model migration."""
from __future__ import annotations
from typing import Dict, Any

from .core import (
    list_models,
    preview_migration,
    execute_migration,
    rollback_migration,
    deactivate_model,
    set_position,
)
from .db import get_history


def route_operation(operation: str, **params) -> Dict[str, Any]:
    """Route operation to handler."""
    try:
        if operation == "models":
            return list_models(
                limit=params.get("limit", 20),
                offset=params.get("offset", 0),
            )

        elif operation == "preview":
            from_id = params.get("from_model_id")
            to_id = params.get("to_model_id")
            if not from_id or not to_id:
                return {
                    "error": "from_model_id and to_model_id are required"
                }
            return preview_migration(
                from_model_id=from_id,
                to_model_id=to_id,
                tenant_id=params.get("tenant_id"),
                company_id=params.get("company_id"),
                creator_id=params.get("creator_id"),
                limit=params.get("limit", 20),
                offset=params.get("offset", 0),
            )

        elif operation == "execute":
            from_id = params.get("from_model_id")
            to_id = params.get("to_model_id")
            if not from_id or not to_id:
                return {
                    "error": "from_model_id and to_model_id are required"
                }
            return execute_migration(
                from_model_id=from_id,
                to_model_id=to_id,
                tenant_id=params.get("tenant_id"),
                company_id=params.get("company_id"),
                creator_id=params.get("creator_id"),
                force=params.get("force", False),
            )

        elif operation == "history":
            return get_history(
                limit=params.get("limit", 10),
                offset=params.get("offset", 0),
            )

        elif operation == "rollback":
            mig_id = params.get("migration_id")
            if not mig_id:
                return {"error": "migration_id is required"}
            return rollback_migration(mig_id)

        elif operation == "deactivate_model":
            mid = params.get("model_id")
            if not mid:
                return {"error": "model_id is required"}
            return deactivate_model(model_id=mid)

        elif operation == "set_position":
            mid = params.get("model_id")
            pos = params.get("position")
            if not mid:
                return {"error": "model_id is required"}
            if pos is None:
                return {"error": "position is required"}
            return set_position(model_id=mid, position=pos)

        else:
            return {"error": f"Unknown operation: {operation}"}

    except Exception as e:
        return {
            "error": f"Operation failed: {str(e)}",
            "error_type": "unknown",
        }
