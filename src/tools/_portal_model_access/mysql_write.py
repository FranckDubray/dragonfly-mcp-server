"""MySQL write operations for portal model access."""
from __future__ import annotations
import logging
from typing import Dict, Any

from .mysql import query, write

LOG = logging.getLogger(__name__)


# ── Tenant model toggle ──────────────────────────────────

def set_tenant_model_active(
    tenant_id: int, model_id: int, active: bool,
) -> Dict[str, Any]:
    """Set active flag on a tenant_model row."""
    val = 1 if active else 0
    return write(
        f"UPDATE tenant_model SET active = {val} "
        f"WHERE tenant_id = {tenant_id} AND model_id = {model_id}"
    )


def set_tenant_editor_active(
    tenant_id: int, editor_id: int, active: bool,
) -> Dict[str, Any]:
    """Toggle all models of an editor for a tenant."""
    val = 1 if active else 0
    return write(
        f"UPDATE tenant_model tm "
        f"JOIN models m ON tm.model_id = m.id "
        f"SET tm.active = {val} "
        f"WHERE tm.tenant_id = {tenant_id} "
        f"AND m.editor_id = {editor_id}"
    )


def count_tenant_editor_models(
    tenant_id: int, editor_id: int,
) -> int:
    """Count how many models an editor has for a tenant."""
    r = query(
        f"SELECT COUNT(*) AS c FROM tenant_model tm "
        f"JOIN models m ON tm.model_id = m.id "
        f"WHERE tm.tenant_id = {tenant_id} "
        f"AND m.editor_id = {editor_id}"
    )
    if "error" in r or not r.get("rows"):
        return 0
    return r["rows"][0].get("c", 0)


# ── Company model toggle ─────────────────────────────────

def set_company_model_active(
    company_id: int, model_id: int, active: bool,
) -> Dict[str, Any]:
    """Set active flag on a company_model row."""
    val = 1 if active else 0
    return write(
        f"UPDATE company_model SET active = {val} "
        f"WHERE company_id = {company_id} AND model_id = {model_id}"
    )


def set_company_editor_active(
    company_id: int, editor_id: int, active: bool,
) -> Dict[str, Any]:
    """Toggle all models of an editor for a company."""
    val = 1 if active else 0
    return write(
        f"UPDATE company_model cm "
        f"JOIN models m ON cm.model_id = m.id "
        f"SET cm.active = {val} "
        f"WHERE cm.company_id = {company_id} "
        f"AND m.editor_id = {editor_id}"
    )


# ── Company inherit toggle ───────────────────────────────

def set_company_inherit_flag(
    company_id: int, inherit: bool,
) -> Dict[str, Any]:
    """Set inherit_models_from_tenant on company."""
    val = 1 if inherit else 0
    return write(
        f"UPDATE company SET inherit_models_from_tenant = {val} "
        f"WHERE id = {company_id}"
    )


# ── Default model ────────────────────────────────────────

def set_tenant_default(
    tenant_id: int, model_id: int,
) -> Dict[str, Any]:
    """Set default chat model for a tenant."""
    return write(
        f"UPDATE tenant SET default_model_id = {model_id} "
        f"WHERE id = {tenant_id}"
    )


def set_company_default(
    company_id: int, model_id: int,
) -> Dict[str, Any]:
    """Set default chat model for a company."""
    return write(
        f"UPDATE company SET default_model_id = {model_id} "
        f"WHERE id = {company_id}"
    )


# ── Whisper model ────────────────────────────────────────

def set_tenant_whisper(
    tenant_id: int, model_id: int,
) -> Dict[str, Any]:
    """Set whisper model for a tenant."""
    return write(
        f"UPDATE tenant SET whisper_model_id = {model_id} "
        f"WHERE id = {tenant_id}"
    )


def set_company_whisper(
    company_id: int, model_id: int,
) -> Dict[str, Any]:
    """Set whisper model for a company."""
    return write(
        f"UPDATE company SET whisper_model_id = {model_id} "
        f"WHERE id = {company_id}"
    )


# ── Sync tenant ──────────────────────────────────────────

def sync_tenant_models(tenant_id: int) -> Dict[str, Any]:
    """Add missing active models to tenant_model. Never removes."""
    r = write(
        f"INSERT IGNORE INTO tenant_model "
        f"(tenant_id, model_id, active, is_default) "
        f"SELECT {tenant_id}, m.id, 1, 0 "
        f"FROM models m "
        f"JOIN editor e ON m.editor_id = e.id "
        f"JOIN tenant_editor te ON te.editor_id = e.id "
        f"  AND te.tenant_id = {tenant_id} "
        f"WHERE m.active = 1"
    )
    if "error" in r:
        return r
    count_r = query(
        f"SELECT COUNT(*) AS total FROM tenant_model "
        f"WHERE tenant_id = {tenant_id}"
    )
    total = 0
    if "error" not in count_r and count_r.get("rows"):
        total = count_r["rows"][0].get("total", 0)
    return {"success": True, "total_after_sync": total}
