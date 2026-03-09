"""Core logic for portal model access management."""
from __future__ import annotations
import logging
from typing import Dict, Any, Optional

from .mysql import (
    get_overview,
    get_tenant_models,
    get_company_info,
    get_company_models,
    get_tenant_companies,
    get_diff,
)
from .mysql_write import (
    set_tenant_model_active,
    set_tenant_editor_active,
    count_tenant_editor_models,
    set_company_model_active,
    set_company_editor_active,
    set_company_inherit_flag,
    set_tenant_default,
    set_company_default,
    set_tenant_whisper,
    set_company_whisper,
    sync_tenant_models,
)

LOG = logging.getLogger(__name__)


# ── overview ──────────────────────────────────────────────

def overview() -> Dict[str, Any]:
    """Global view of all tenants with model counts."""
    r = get_overview()
    if "error" in r:
        return r
    return {"tenants": r.get("rows", []), "count": len(r.get("rows", []))}


# ── tenant_models ─────────────────────────────────────────

def tenant_models(
    tenant_id: int,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """List models for a tenant with editor grouping."""
    r = get_tenant_models(tenant_id, category, limit, offset)
    if "error" in r:
        return r
    companies = get_tenant_companies(tenant_id)
    r["tenant_id"] = tenant_id
    r["companies"] = (
        companies.get("rows", []) if "error" not in companies else []
    )
    return r


# ── company_models ────────────────────────────────────────

def company_models(
    company_id: int,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """List models for a company."""
    info = get_company_info(company_id)
    if "error" in info or not info.get("rows"):
        return {"error": f"Company {company_id} not found"}
    r = get_company_models(company_id, category, limit, offset)
    if "error" in r:
        return r
    r["company"] = info["rows"][0]
    return r


# ── set_tenant_model ──────────────────────────────────────

def toggle_tenant_model(
    tenant_id: int, model_id: int, active: bool,
) -> Dict[str, Any]:
    """Toggle a single model for a tenant."""
    r = set_tenant_model_active(tenant_id, model_id, active)
    if "error" in r:
        return r
    state = "activated" if active else "deactivated"
    LOG.info("🔧 Tenant %d: model %d %s", tenant_id, model_id, state)
    return {
        "tenant_id": tenant_id,
        "model_id": model_id,
        "active": active,
    }


# ── set_tenant_editor ─────────────────────────────────────

def toggle_tenant_editor(
    tenant_id: int, editor_id: int, active: bool,
) -> Dict[str, Any]:
    """Toggle all models of an editor for a tenant."""
    count = count_tenant_editor_models(tenant_id, editor_id)
    if count == 0:
        return {
            "error": f"No models for editor {editor_id} "
            f"in tenant {tenant_id}",
        }
    r = set_tenant_editor_active(tenant_id, editor_id, active)
    if "error" in r:
        return r
    state = "activated" if active else "deactivated"
    LOG.info(
        "🔧 Tenant %d: editor %d (%d models) %s",
        tenant_id, editor_id, count, state,
    )
    return {
        "tenant_id": tenant_id,
        "editor_id": editor_id,
        "models_affected": count,
        "active": active,
    }


# ── set_company_model ─────────────────────────────────────

def toggle_company_model(
    company_id: int, model_id: int, active: bool,
) -> Dict[str, Any]:
    """Toggle a single model for a company."""
    r = set_company_model_active(company_id, model_id, active)
    if "error" in r:
        return r
    state = "activated" if active else "deactivated"
    LOG.info("🔧 Company %d: model %d %s", company_id, model_id, state)
    return {
        "company_id": company_id,
        "model_id": model_id,
        "active": active,
    }


# ── set_company_editor ────────────────────────────────────

def toggle_company_editor(
    company_id: int, editor_id: int, active: bool,
) -> Dict[str, Any]:
    """Toggle all models of an editor for a company."""
    r = set_company_editor_active(company_id, editor_id, active)
    if "error" in r:
        return r
    state = "activated" if active else "deactivated"
    LOG.info("🔧 Company %d: editor %d %s", company_id, editor_id, state)
    return {
        "company_id": company_id,
        "editor_id": editor_id,
        "active": active,
    }


# ── set_company_inherit ───────────────────────────────────

def toggle_company_inherit(
    company_id: int, inherit: bool,
) -> Dict[str, Any]:
    """Switch company between inherit and custom mode."""
    r = set_company_inherit_flag(company_id, inherit)
    if "error" in r:
        return r
    mode = "inherit" if inherit else "custom"
    LOG.info("🔧 Company %d: switched to %s", company_id, mode)
    return {
        "company_id": company_id,
        "inherit_models_from_tenant": inherit,
    }


# ── set_default ───────────────────────────────────────────

def set_default_model(
    model_id: int,
    tenant_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Set default chat model for tenant or company."""
    if tenant_id:
        r = set_tenant_default(tenant_id, model_id)
        target = f"tenant {tenant_id}"
    elif company_id:
        r = set_company_default(company_id, model_id)
        target = f"company {company_id}"
    else:
        return {"error": "tenant_id or company_id required"}
    if "error" in r:
        return r
    LOG.info("⭐ %s: default model → %d", target, model_id)
    return {
        "tenant_id": tenant_id,
        "company_id": company_id,
        "default_model_id": model_id,
    }


# ── set_whisper ───────────────────────────────────────────

def set_whisper_model(
    model_id: int,
    tenant_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Set whisper model for tenant or company."""
    if tenant_id:
        r = set_tenant_whisper(tenant_id, model_id)
        target = f"tenant {tenant_id}"
    elif company_id:
        r = set_company_whisper(company_id, model_id)
        target = f"company {company_id}"
    else:
        return {"error": "tenant_id or company_id required"}
    if "error" in r:
        return r
    LOG.info("🎤 %s: whisper model → %d", target, model_id)
    return {
        "tenant_id": tenant_id,
        "company_id": company_id,
        "whisper_model_id": model_id,
    }


# ── sync_tenant ───────────────────────────────────────────

def sync_tenant(tenant_id: int) -> Dict[str, Any]:
    """Resync models for a tenant from its editors."""
    r = sync_tenant_models(tenant_id)
    if "error" in r:
        return r
    LOG.info(
        "🔄 Tenant %d synced: %d models",
        tenant_id, r.get("total_after_sync", 0),
    )
    return {
        "tenant_id": tenant_id,
        "total_models": r.get("total_after_sync", 0),
    }


# ── diff ──────────────────────────────────────────────────

def diff_tenant_company(
    tenant_id: int, company_id: int,
    limit: int = 50, offset: int = 0,
) -> Dict[str, Any]:
    """Compare models between tenant and company."""
    r = get_diff(tenant_id, company_id, limit, offset)
    if "error" in r:
        return r
    return {
        "tenant_id": tenant_id,
        "company_id": company_id,
        "rows": r.get("rows", []),
        "returned_count": r.get("returned_count", 0),
    }
