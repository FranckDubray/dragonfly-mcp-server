"""MySQL operations via SSH (reuses portal_db infrastructure)."""
from __future__ import annotations
import logging
from typing import Dict, Any, List, Optional

# Reuse portal_db SSH + MySQL infrastructure
from tools._portal_db.utils import run_mysql_via_ssh, parse_tsv

LOG = logging.getLogger(__name__)


def query_mysql(sql: str, timeout: int = 30) -> Dict[str, Any]:
    """Execute read-only query, return parsed result."""
    result = run_mysql_via_ssh(sql, timeout=timeout)
    if not result["success"]:
        return {"error": result["error"]}
    return parse_tsv(result["stdout"])


def write_mysql(sql: str, timeout: int = 30) -> Dict[str, Any]:
    """Execute write query (UPDATE), return raw result."""
    result = run_mysql_via_ssh(sql, timeout=timeout)
    if not result["success"]:
        return {"error": result["error"]}
    # For UPDATE, stdout may be empty — that's OK
    return {"success": True, "stdout": result["stdout"]}


def get_model_info(model_id: int) -> Optional[Dict[str, Any]]:
    """Get model info by ID."""
    r = query_mysql(
        f"SELECT id, name, display_name, active, position "
        f"FROM models WHERE id = {model_id}"
    )
    if "error" in r or not r.get("rows"):
        return None
    return r["rows"][0]


def get_assistants_by_model(
    model_id: int,
    tenant_id: Optional[int] = None,
    company_id: Optional[int] = None,
    creator_id: Optional[int] = None,
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    """Get assistants using a specific model, with optional filters."""
    # Base query
    select = (
        "SELECT a.id, a.name, a.model_ai_id, a.creator_id, "
        "u.email as creator_email"
    )
    from_clause = " FROM assistant a LEFT JOIN user u ON a.creator_id = u.id"
    where = f" WHERE a.model_ai_id = {model_id}"

    # Optional filters via JOIN
    joins = ""
    if tenant_id is not None:
        joins += " JOIN assistant_tenant at2 ON a.id = at2.assistant_id"
        where += f" AND at2.tenant_id = {tenant_id}"
    if company_id is not None:
        joins += " JOIN assistant_company ac ON a.id = ac.assistant_id"
        where += f" AND ac.company_id = {company_id}"
    if creator_id is not None:
        where += f" AND a.creator_id = {creator_id}"

    # Count query
    count_sql = f"SELECT COUNT(*) as total{from_clause}{joins}{where}"
    count_r = query_mysql(count_sql)
    total = 0
    if "error" not in count_r and count_r.get("rows"):
        total = count_r["rows"][0].get("total", 0)

    # Data query (paginated)
    data_sql = (
        f"{select}{from_clause}{joins}{where}"
        f" ORDER BY a.id LIMIT {limit} OFFSET {offset}"
    )
    data_r = query_mysql(data_sql)
    if "error" in data_r:
        return data_r

    return {
        "rows": data_r.get("rows", []),
        "returned_count": data_r.get("returned_count", 0),
        "total_count": total,
        "has_more": (offset + data_r.get("returned_count", 0)) < total,
    }


def update_model_batch(
    assistant_ids: List[int],
    new_model_id: int,
) -> Dict[str, Any]:
    """Update model_ai_id for a list of assistants."""
    if not assistant_ids:
        return {"error": "No assistant IDs provided"}

    ids_str = ",".join(str(i) for i in assistant_ids)
    sql = (
        f"UPDATE assistant SET model_ai_id = {new_model_id} "
        f"WHERE id IN ({ids_str})"
    )
    return write_mysql(sql, timeout=60)


def set_model_active(model_id: int, active: bool) -> Dict[str, Any]:
    """Set model active flag (0 or 1). NEVER deletes."""
    val = 1 if active else 0
    sql = f"UPDATE models SET active = {val} WHERE id = {model_id}"
    return write_mysql(sql, timeout=30)


def set_model_position(model_id: int, position: int) -> Dict[str, Any]:
    """Set model display position."""
    sql = f"UPDATE models SET position = {position} WHERE id = {model_id}"
    return write_mysql(sql, timeout=30)


def count_assistants_on_model(model_id: int) -> int:
    """Count assistants currently using a model."""
    r = query_mysql(
        f"SELECT COUNT(*) as total FROM assistant "
        f"WHERE model_ai_id = {model_id}"
    )
    if "error" in r or not r.get("rows"):
        return -1
    return r["rows"][0].get("total", 0)


def get_default_model_refs(model_id: int) -> Dict[str, Any]:
    """Check if model is used as default in tenants/companies."""
    tenants_r = query_mysql(
        f"SELECT id, name FROM tenant "
        f"WHERE default_model_id = {model_id}"
    )
    companies_r = query_mysql(
        f"SELECT id, name FROM company "
        f"WHERE default_model_id = {model_id}"
    )
    return {
        "tenants": tenants_r.get("rows", []) if "error" not in tenants_r else [],
        "companies": companies_r.get("rows", []) if "error" not in companies_r else [],
    }
