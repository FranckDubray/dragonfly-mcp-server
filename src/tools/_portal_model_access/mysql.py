"""MySQL operations for portal model access — read queries."""
from __future__ import annotations
import logging
from typing import Dict, Any

from tools._portal_db.utils import run_mysql_via_ssh, parse_tsv

LOG = logging.getLogger(__name__)


def query(sql: str, timeout: int = 30) -> Dict[str, Any]:
    """Execute read query (TSV mode)."""
    result = run_mysql_via_ssh(sql, timeout=timeout)
    if not result["success"]:
        return {"error": result["error"]}
    return parse_tsv(result["stdout"])


def write(sql: str, timeout: int = 30) -> Dict[str, Any]:
    """Execute write query."""
    result = run_mysql_via_ssh(sql, timeout=timeout)
    if not result["success"]:
        return {"error": result["error"]}
    return {"success": True, "stdout": result["stdout"]}


# ── READ: Overview ────────────────────────────────────────

def get_overview() -> Dict[str, Any]:
    """Get all tenants with model/company counts."""
    return query(
        "SELECT t.id, t.name, "
        "t.inherit_models_from_editors AS inherit_editors, "
        "t.default_model_id, dm.display_name AS default_model, "
        "t.whisper_model_id, wm.display_name AS whisper_model, "
        "(SELECT COUNT(*) FROM tenant_model tm "
        " WHERE tm.tenant_id = t.id AND tm.active = 1) AS models_active, "
        "(SELECT COUNT(*) FROM tenant_model tm "
        " WHERE tm.tenant_id = t.id AND tm.active = 0) AS models_inactive, "
        "(SELECT COUNT(*) FROM company c "
        " WHERE c.tenant_id = t.id) AS nb_companies "
        "FROM tenant t "
        "LEFT JOIN models dm ON t.default_model_id = dm.id "
        "LEFT JOIN models wm ON t.whisper_model_id = wm.id "
        "ORDER BY t.id"
    )


# ── READ: Tenant models ──────────────────────────────────

def get_tenant_models(
    tenant_id: int, category: str = None,
    limit: int = 50, offset: int = 0,
) -> Dict[str, Any]:
    """Get models for a tenant grouped by editor + category."""
    cat_filter = ""
    if category:
        safe_cat = category.replace("'", "\\'")
        cat_filter = f" AND m.category = '{safe_cat}'"

    count_r = query(
        f"SELECT COUNT(*) AS total FROM tenant_model tm "
        f"JOIN models m ON tm.model_id = m.id "
        f"WHERE tm.tenant_id = {tenant_id}{cat_filter}"
    )
    total = 0
    if "error" not in count_r and count_r.get("rows"):
        total = count_r["rows"][0].get("total", 0)

    data_r = query(
        f"SELECT tm.id AS tm_id, tm.active AS tenant_active, "
        f"m.id AS model_id, m.name, m.display_name, "
        f"m.category, m.active AS global_active, m.position, "
        f"e.id AS editor_id, e.name AS editor_name, "
        f"CASE WHEN m.config LIKE '%\"onlyApi\": true%' "
        f"  THEN 1 ELSE 0 END AS is_api_only "
        f"FROM tenant_model tm "
        f"JOIN models m ON tm.model_id = m.id "
        f"JOIN editor e ON m.editor_id = e.id "
        f"WHERE tm.tenant_id = {tenant_id}{cat_filter} "
        f"ORDER BY e.name, m.category, m.position, m.name "
        f"LIMIT {limit} OFFSET {offset}"
    )
    if "error" in data_r:
        return data_r

    return {
        "rows": data_r.get("rows", []),
        "returned_count": data_r.get("returned_count", 0),
        "total_count": total,
        "has_more": (offset + data_r.get("returned_count", 0)) < total,
    }


# ── READ: Company ────────────────────────────────────────

def get_company_info(company_id: int) -> Dict[str, Any]:
    """Get company info with inherit flags."""
    return query(
        f"SELECT c.id, c.name, c.tenant_id, t.name AS tenant_name, "
        f"c.inherit_models_from_tenant, c.inherit_whisper_from_tenant, "
        f"c.default_model_id, dm.display_name AS default_model, "
        f"c.whisper_model_id, wm.display_name AS whisper_model "
        f"FROM company c "
        f"JOIN tenant t ON c.tenant_id = t.id "
        f"LEFT JOIN models dm ON c.default_model_id = dm.id "
        f"LEFT JOIN models wm ON c.whisper_model_id = wm.id "
        f"WHERE c.id = {company_id}"
    )


def get_company_models(
    company_id: int, category: str = None,
    limit: int = 50, offset: int = 0,
) -> Dict[str, Any]:
    """Get models for a company (from company_model)."""
    cat_filter = ""
    if category:
        safe_cat = category.replace("'", "\\'")
        cat_filter = f" AND m.category = '{safe_cat}'"

    count_r = query(
        f"SELECT COUNT(*) AS total FROM company_model cm "
        f"JOIN models m ON cm.model_id = m.id "
        f"WHERE cm.company_id = {company_id}{cat_filter}"
    )
    total = 0
    if "error" not in count_r and count_r.get("rows"):
        total = count_r["rows"][0].get("total", 0)

    data_r = query(
        f"SELECT cm.id AS cm_id, cm.active AS company_active, "
        f"cm.inherit_from_tenant, "
        f"m.id AS model_id, m.name, m.display_name, "
        f"m.category, m.active AS global_active, m.position, "
        f"e.id AS editor_id, e.name AS editor_name, "
        f"CASE WHEN m.config LIKE '%\"onlyApi\": true%' "
        f"  THEN 1 ELSE 0 END AS is_api_only "
        f"FROM company_model cm "
        f"JOIN models m ON cm.model_id = m.id "
        f"JOIN editor e ON m.editor_id = e.id "
        f"WHERE cm.company_id = {company_id}{cat_filter} "
        f"ORDER BY e.name, m.category, m.position, m.name "
        f"LIMIT {limit} OFFSET {offset}"
    )
    if "error" in data_r:
        return data_r

    return {
        "rows": data_r.get("rows", []),
        "returned_count": data_r.get("returned_count", 0),
        "total_count": total,
        "has_more": (offset + data_r.get("returned_count", 0)) < total,
    }


def get_tenant_companies(tenant_id: int) -> Dict[str, Any]:
    """List companies under a tenant."""
    return query(
        f"SELECT c.id, c.name, c.inherit_models_from_tenant, "
        f"c.default_model_id, c.whisper_model_id, "
        f"(SELECT COUNT(*) FROM company_model cm "
        f"  WHERE cm.company_id = c.id) AS nb_models "
        f"FROM company c WHERE c.tenant_id = {tenant_id} "
        f"ORDER BY c.name"
    )


# ── READ: Diff ────────────────────────────────────────────

def get_diff(
    tenant_id: int, company_id: int,
    limit: int = 50, offset: int = 0,
) -> Dict[str, Any]:
    """Compare models between tenant and company."""
    return query(
        f"SELECT m.id AS model_id, m.name, m.display_name, "
        f"m.category, e.name AS editor_name, "
        f"tm.active AS tenant_active, "
        f"cm.active AS company_active, "
        f"cm.inherit_from_tenant, "
        f"CASE WHEN m.config LIKE '%\"onlyApi\": true%' "
        f"  THEN 1 ELSE 0 END AS is_api_only "
        f"FROM tenant_model tm "
        f"JOIN models m ON tm.model_id = m.id "
        f"JOIN editor e ON m.editor_id = e.id "
        f"LEFT JOIN company_model cm "
        f"  ON cm.model_id = m.id AND cm.company_id = {company_id} "
        f"WHERE tm.tenant_id = {tenant_id} "
        f"ORDER BY e.name, m.category, m.position, m.name "
        f"LIMIT {limit} OFFSET {offset}"
    )
