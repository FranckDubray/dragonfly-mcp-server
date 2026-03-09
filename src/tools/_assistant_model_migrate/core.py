"""Core business logic for assistant model migration."""
from __future__ import annotations
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from .mysql import (
    query_mysql,
    get_model_info,
    get_assistants_by_model,
    update_model_batch,
    set_model_active,
    set_model_position,
    count_assistants_on_model,
    get_default_model_refs,
)
from .db import (
    save_migration,
    get_history,
    get_migration_details,
    mark_rolled_back,
)

LOG = logging.getLogger(__name__)

_MAX_WITHOUT_FORCE = 500


def list_models(limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    """List models with assistant counts."""
    sql = (
        "SELECT m.id, m.name, m.display_name, m.active, "
        "e.name as editor, COUNT(a.id) as nb_assistants "
        "FROM models m "
        "JOIN editor e ON m.editor_id = e.id "
        "LEFT JOIN assistant a ON a.model_ai_id = m.id "
        "GROUP BY m.id "
        "HAVING nb_assistants > 0 "
        "ORDER BY nb_assistants DESC "
        f"LIMIT {limit} OFFSET {offset}"
    )
    r = query_mysql(sql)
    if "error" in r:
        return r

    # Get total count
    count_sql = (
        "SELECT COUNT(*) as total FROM ("
        "SELECT m.id FROM models m "
        "LEFT JOIN assistant a ON a.model_ai_id = m.id "
        "GROUP BY m.id HAVING COUNT(a.id) > 0"
        ") sub"
    )
    cr = query_mysql(count_sql)
    total = cr["rows"][0]["total"] if "rows" in cr and cr["rows"] else 0

    return {
        "models": r.get("rows", []),
        "returned_count": r.get("returned_count", 0),
        "total_count": total,
        "has_more": (offset + r.get("returned_count", 0)) < total,
    }


def preview_migration(
    from_model_id: int,
    to_model_id: int,
    tenant_id: Optional[int] = None,
    company_id: Optional[int] = None,
    creator_id: Optional[int] = None,
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    """Preview migration — dry run, no changes."""
    # Validate models exist
    from_model = get_model_info(from_model_id)
    if not from_model:
        return {"error": f"Source model {from_model_id} not found"}

    to_model = get_model_info(to_model_id)
    if not to_model:
        return {"error": f"Target model {to_model_id} not found"}

    # Get impacted assistants
    result = get_assistants_by_model(
        from_model_id,
        tenant_id=tenant_id,
        company_id=company_id,
        creator_id=creator_id,
        limit=limit,
        offset=offset,
    )
    if "error" in result:
        return result

    filters = {}
    if tenant_id:
        filters["tenant_id"] = tenant_id
    if company_id:
        filters["company_id"] = company_id
    if creator_id:
        filters["creator_id"] = creator_id

    return {
        "dry_run": True,
        "from_model": from_model,
        "to_model": to_model,
        "filters": filters or None,
        "affected_count": result["total_count"],
        "assistants": result["rows"],
        "returned_count": result["returned_count"],
        "has_more": result["has_more"],
        "offset": offset,
        "limit": limit,
    }


def execute_migration(
    from_model_id: int,
    to_model_id: int,
    tenant_id: Optional[int] = None,
    company_id: Optional[int] = None,
    creator_id: Optional[int] = None,
    force: bool = False,
) -> Dict[str, Any]:
    """Execute migration — real UPDATE."""
    # Validate models
    from_model = get_model_info(from_model_id)
    if not from_model:
        return {"error": f"Source model {from_model_id} not found"}

    to_model = get_model_info(to_model_id)
    if not to_model:
        return {"error": f"Target model {to_model_id} not found"}

    if not to_model.get("active"):
        return {
            "error": f"Target model '{to_model.get('name')}' is not active"
        }

    if from_model_id == to_model_id:
        return {"error": "Source and target models are the same"}

    # Get ALL impacted assistants (no pagination — need full list)
    all_assistants = get_assistants_by_model(
        from_model_id,
        tenant_id=tenant_id,
        company_id=company_id,
        creator_id=creator_id,
        limit=10000,
        offset=0,
    )
    if "error" in all_assistants:
        return all_assistants

    total = all_assistants["total_count"]
    if total == 0:
        return {"error": "No assistants match the criteria"}

    if total > _MAX_WITHOUT_FORCE and not force:
        return {
            "error": (
                f"Migration would affect {total} assistants "
                f"(> {_MAX_WITHOUT_FORCE}). Use force=true to proceed."
            ),
            "affected_count": total,
        }

    # Build details for log
    assistant_ids = []
    details = []
    for a in all_assistants["rows"]:
        aid = a["id"]
        assistant_ids.append(aid)
        details.append({
            "assistant_id": aid,
            "assistant_name": a.get("name"),
            "old_model_ai_id": from_model_id,
            "new_model_ai_id": to_model_id,
        })

    # Execute UPDATE
    result = update_model_batch(assistant_ids, to_model_id)
    if "error" in result:
        return result

    # Save migration log
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    mig_id = "mig_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    filters = {}
    if tenant_id:
        filters["tenant_id"] = tenant_id
    if company_id:
        filters["company_id"] = company_id
    if creator_id:
        filters["creator_id"] = creator_id

    save_migration(
        migration_id=mig_id,
        created_at=now,
        from_model_id=from_model_id,
        from_model_name=from_model.get("name", ""),
        to_model_id=to_model_id,
        to_model_name=to_model.get("name", ""),
        filters=json.dumps(filters) if filters else None,
        affected_count=total,
        details=details,
    )

    LOG.info(
        "✅ Migration %s: %d assistants %s → %s",
        mig_id, total, from_model.get("name"), to_model.get("name"),
    )

    return {
        "migration_id": mig_id,
        "migrated": total,
        "from_model": from_model,
        "to_model": to_model,
        "filters": filters or None,
    }


def deactivate_model(model_id: int) -> Dict[str, Any]:
    """Deactivate a model (set active=0). NEVER deletes.

    Refuses if assistants still use this model.
    Warns if model is default for tenants/companies.
    """
    # Check model exists
    model = get_model_info(model_id)
    if not model:
        return {"error": f"Model {model_id} not found"}

    # Already inactive?
    if not model.get("active"):
        return {
            "error": (
                f"Model '{model.get('name')}' (id={model_id}) "
                f"is already inactive"
            ),
            "model": model,
        }

    # BLOCKER: check assistants still using it
    nb_assistants = count_assistants_on_model(model_id)
    if nb_assistants < 0:
        return {"error": "Could not check assistant count"}

    if nb_assistants > 0:
        return {
            "error": (
                f"Cannot deactivate: {nb_assistants} assistant(s) "
                f"still use model '{model.get('name')}' (id={model_id}). "
                f"Migrate them first with preview/execute."
            ),
            "remaining_assistants": nb_assistants,
            "model": model,
        }

    # WARNING: check default_model refs (non-blocking)
    refs = get_default_model_refs(model_id)
    warnings = []
    if refs["tenants"]:
        names = ", ".join(t["name"] for t in refs["tenants"])
        warnings.append(
            f"Model is default for tenant(s): {names}"
        )
    if refs["companies"]:
        names = ", ".join(c["name"] for c in refs["companies"])
        warnings.append(
            f"Model is default for company/companies: {names}"
        )

    # Execute deactivation
    result = set_model_active(model_id, active=False)
    if "error" in result:
        return result

    LOG.info(
        "🔒 Model '%s' (id=%d) deactivated",
        model.get("name"), model_id,
    )

    response: Dict[str, Any] = {
        "deactivated": True,
        "model_id": model_id,
        "model_name": model.get("name"),
        "display_name": model.get("display_name"),
    }

    if warnings:
        response["warnings"] = warnings

    return response


def set_position(model_id: int, position: int) -> Dict[str, Any]:
    """Change the display position of a model.

    Args:
        model_id: ID of the model
        position: New position (0 = top, 99 = bottom of list)
    """
    # Check model exists
    model = get_model_info(model_id)
    if not model:
        return {"error": f"Model {model_id} not found"}

    old_position = model.get("position")

    # Execute update
    result = set_model_position(model_id, position)
    if "error" in result:
        return result

    LOG.info(
        "📍 Model '%s' (id=%d) position: %s → %d",
        model.get("name"), model_id, old_position, position,
    )

    return {
        "model_id": model_id,
        "model_name": model.get("name"),
        "display_name": model.get("display_name"),
        "old_position": old_position,
        "new_position": position,
    }


def rollback_migration(migration_id: str) -> Dict[str, Any]:
    """Rollback a migration."""
    details = get_migration_details(migration_id)
    if not details:
        return {"error": f"Migration '{migration_id}' not found"}

    # Group by old_model_ai_id for batch updates
    by_old_model: Dict[int, list] = {}
    for d in details:
        old_id = d["old_model_ai_id"]
        if old_id not in by_old_model:
            by_old_model[old_id] = []
        by_old_model[old_id].append(d["assistant_id"])

    # Execute rollback updates
    total_rolled = 0
    for old_model_id, assistant_ids in by_old_model.items():
        result = update_model_batch(assistant_ids, old_model_id)
        if "error" in result:
            return {
                "error": f"Rollback partially failed: {result['error']}",
                "rolled_back_so_far": total_rolled,
            }
        total_rolled += len(assistant_ids)

    # Mark as rolled back
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    mark_rolled_back(migration_id, now)

    LOG.info("↩️ Rollback %s: %d assistants restored", migration_id, total_rolled)

    return {
        "migration_id": migration_id,
        "rolled_back": total_rolled,
    }
