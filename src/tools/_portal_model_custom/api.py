"""API routing for custom model management."""
from __future__ import annotations
from typing import Dict, Any

from .core import (
    list_customs,
    preview_create,
    create_custom,
    set_active,
    set_position,
    set_preprompt,
    list_model_tools,
    add_tools,
    remove_tools,
    update_model,
)


def route_operation(operation: str, **params) -> Dict[str, Any]:
    """Route operation to handler."""
    try:
        if operation == "list":
            return list_customs(
                limit=params.get("limit", 20),
                offset=params.get("offset", 0),
            )

        elif operation == "preview":
            src = params.get("source_model_id")
            name = params.get("name")
            dn = params.get("display_name")
            if not src or not name or not dn:
                return {
                    "error": "source_model_id, name, and "
                    "display_name are required"
                }
            return preview_create(src, name, dn)

        elif operation == "create":
            src = params.get("source_model_id")
            name = params.get("name")
            dn = params.get("display_name")
            if not src or not name or not dn:
                return {
                    "error": "source_model_id, name, and "
                    "display_name are required"
                }
            return create_custom(src, name, dn)

        elif operation == "activate":
            mid = params.get("model_id")
            active = params.get("active")
            if not mid or active is None:
                return {"error": "model_id and active are required"}
            return set_active(mid, bool(active))

        elif operation == "set_position":
            mid = params.get("model_id")
            pos = params.get("position")
            if not mid or pos is None:
                return {"error": "model_id and position are required"}
            return set_position(mid, pos)

        elif operation == "set_preprompt":
            mid = params.get("model_id")
            pp = params.get("preprompt")
            if not mid:
                return {"error": "model_id is required"}
            return set_preprompt(mid, pp or "")

        elif operation == "add_tools":
            mid = params.get("model_id")
            tids = params.get("tool_ids")
            if not mid or not tids:
                return {"error": "model_id and tool_ids are required"}
            return add_tools(mid, tids)

        elif operation == "remove_tools":
            mid = params.get("model_id")
            tids = params.get("tool_ids")
            if not mid or not tids:
                return {"error": "model_id and tool_ids are required"}
            return remove_tools(mid, tids)

        elif operation == "list_tools":
            mid = params.get("model_id")
            if not mid:
                return {"error": "model_id is required"}
            return list_model_tools(
                mid,
                limit=params.get("limit", 20),
                offset=params.get("offset", 0),
            )

        elif operation == "update":
            mid = params.get("model_id")
            if not mid:
                return {"error": "model_id is required"}
            return update_model(
                mid,
                display_name=params.get("display_name"),
                config=params.get("config"),
                input_json=params.get("input"),
            )

        else:
            return {"error": f"Unknown operation: {operation}"}

    except Exception as e:
        return {
            "error": f"Operation failed: {str(e)}",
            "error_type": "unknown",
        }
