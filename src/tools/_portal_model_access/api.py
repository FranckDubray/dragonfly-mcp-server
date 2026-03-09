"""API routing for portal model access management."""
from __future__ import annotations
from typing import Dict, Any

from .core import (
    overview,
    tenant_models,
    company_models,
    toggle_tenant_model,
    toggle_tenant_editor,
    toggle_company_model,
    toggle_company_editor,
    toggle_company_inherit,
    set_default_model,
    set_whisper_model,
    sync_tenant,
    diff_tenant_company,
)


def route_operation(operation: str, **p) -> Dict[str, Any]:
    """Route operation to the correct handler."""
    try:
        if operation == "overview":
            return overview()

        elif operation == "tenant_models":
            if not p.get("tenant_id"):
                return {"error": "tenant_id is required"}
            return tenant_models(
                p["tenant_id"],
                category=p.get("category"),
                limit=p.get("limit", 50),
                offset=p.get("offset", 0),
            )

        elif operation == "company_models":
            if not p.get("company_id"):
                return {"error": "company_id is required"}
            return company_models(
                p["company_id"],
                category=p.get("category"),
                limit=p.get("limit", 50),
                offset=p.get("offset", 0),
            )

        elif operation == "set_tenant_model":
            if not p.get("tenant_id") or not p.get("model_id"):
                return {"error": "tenant_id and model_id required"}
            if p.get("active") is None:
                return {"error": "active is required"}
            return toggle_tenant_model(
                p["tenant_id"], p["model_id"], bool(p["active"]),
            )

        elif operation == "set_tenant_editor":
            if not p.get("tenant_id") or not p.get("editor_id"):
                return {"error": "tenant_id and editor_id required"}
            if p.get("active") is None:
                return {"error": "active is required"}
            return toggle_tenant_editor(
                p["tenant_id"], p["editor_id"], bool(p["active"]),
            )

        elif operation == "set_company_model":
            if not p.get("company_id") or not p.get("model_id"):
                return {"error": "company_id and model_id required"}
            if p.get("active") is None:
                return {"error": "active is required"}
            return toggle_company_model(
                p["company_id"], p["model_id"], bool(p["active"]),
            )

        elif operation == "set_company_editor":
            if not p.get("company_id") or not p.get("editor_id"):
                return {"error": "company_id and editor_id required"}
            if p.get("active") is None:
                return {"error": "active is required"}
            return toggle_company_editor(
                p["company_id"], p["editor_id"], bool(p["active"]),
            )

        elif operation == "set_company_inherit":
            if not p.get("company_id"):
                return {"error": "company_id is required"}
            if p.get("inherit") is None:
                return {"error": "inherit is required"}
            return toggle_company_inherit(
                p["company_id"], bool(p["inherit"]),
            )

        elif operation == "set_default":
            if not p.get("model_id"):
                return {"error": "model_id is required"}
            if not p.get("tenant_id") and not p.get("company_id"):
                return {"error": "tenant_id or company_id required"}
            return set_default_model(
                p["model_id"],
                tenant_id=p.get("tenant_id"),
                company_id=p.get("company_id"),
            )

        elif operation == "set_whisper":
            if not p.get("model_id"):
                return {"error": "model_id is required"}
            if not p.get("tenant_id") and not p.get("company_id"):
                return {"error": "tenant_id or company_id required"}
            return set_whisper_model(
                p["model_id"],
                tenant_id=p.get("tenant_id"),
                company_id=p.get("company_id"),
            )

        elif operation == "sync_tenant":
            if not p.get("tenant_id"):
                return {"error": "tenant_id is required"}
            return sync_tenant(p["tenant_id"])

        elif operation == "diff":
            if not p.get("tenant_id") or not p.get("company_id"):
                return {"error": "tenant_id and company_id required"}
            return diff_tenant_company(
                p["tenant_id"], p["company_id"],
                limit=p.get("limit", 50),
                offset=p.get("offset", 0),
            )

        else:
            return {"error": f"Unknown operation: {operation}"}

    except Exception as e:
        return {
            "error": f"Operation failed: {str(e)}",
            "error_type": "unknown",
        }
