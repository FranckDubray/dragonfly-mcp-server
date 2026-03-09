"""Core business logic for Portal DB (read-only)."""
from __future__ import annotations
from typing import Dict, Any
import logging

from .validators import (
    validate_sql_read_only,
    validate_table_name,
    validate_where_clause,
)
from .utils import run_mysql_via_ssh, parse_tsv

LOG = logging.getLogger(__name__)


def execute_query(
    sql: str,
    limit: int = 50,
    offset: int = 0,
    timeout: int = 30,
) -> Dict[str, Any]:
    """Execute a read-only SQL query with pagination."""
    # Validate read-only
    valid, error = validate_sql_read_only(sql)
    if not valid:
        return {"error": error, "error_type": "validation"}

    # Inject LIMIT/OFFSET if not already present
    sql_lower = sql.strip().rstrip(";").lower()
    has_limit = " limit " in sql_lower
    has_offset = " offset " in sql_lower

    final_sql = sql.strip().rstrip(";")
    if not has_limit:
        final_sql += f" LIMIT {limit}"
    if not has_offset and offset > 0:
        final_sql += f" OFFSET {offset}"

    # Also run a COUNT query for total
    count_result = _get_total_count(sql, timeout)

    # Execute main query
    result = run_mysql_via_ssh(final_sql, timeout=timeout)
    if not result["success"]:
        return {"error": result["error"], "error_type": "mysql"}

    parsed = parse_tsv(result["stdout"])
    parsed["offset"] = offset
    parsed["limit"] = limit

    if count_result is not None:
        parsed["total_count"] = count_result
        parsed["has_more"] = (offset + parsed["returned_count"]) < count_result

    LOG.info(
        "✅ Query OK: %d rows returned (total: %s)",
        parsed["returned_count"],
        count_result,
    )
    return parsed


def _get_total_count(sql: str, timeout: int) -> int | None:
    """Try to get total count for a SELECT query."""
    try:
        sql_clean = sql.strip().rstrip(";")
        # Wrap the original query (without LIMIT) as subquery
        count_sql = f"SELECT COUNT(*) as total FROM ({sql_clean}) AS _cnt"
        result = run_mysql_via_ssh(count_sql, timeout=timeout)
        if result["success"]:
            parsed = parse_tsv(result["stdout"])
            if parsed["rows"]:
                return parsed["rows"][0].get("total")
    except Exception as e:
        LOG.debug("Could not get total count: %s", e)
    return None


def list_tables(timeout: int = 30) -> Dict[str, Any]:
    """List all tables in the database."""
    result = run_mysql_via_ssh("SHOW TABLES", timeout=timeout)
    if not result["success"]:
        return {"error": result["error"], "error_type": "mysql"}

    parsed = parse_tsv(result["stdout"])
    # Flatten to simple list
    tables = []
    for row in parsed["rows"]:
        for v in row.values():
            tables.append(v)

    LOG.info("✅ %d tables found", len(tables))
    return {"tables": tables, "count": len(tables)}


def describe_table(
    table: str, timeout: int = 30
) -> Dict[str, Any]:
    """Describe a table's structure."""
    valid, error = validate_table_name(table)
    if not valid:
        return {"error": error, "error_type": "validation"}

    result = run_mysql_via_ssh(f"DESCRIBE `{table}`", timeout=timeout)
    if not result["success"]:
        return {"error": result["error"], "error_type": "mysql"}

    parsed = parse_tsv(result["stdout"])
    LOG.info("✅ Table '%s': %d columns", table, parsed["returned_count"])
    return {"table": table, **parsed}


def get_schema(timeout: int = 60) -> Dict[str, Any]:
    """Get full database schema (all tables, all columns)."""
    sql = (
        "SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, "
        "COLUMN_KEY, COLUMN_DEFAULT, EXTRA "
        "FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() "
        "ORDER BY TABLE_NAME, ORDINAL_POSITION"
    )
    result = run_mysql_via_ssh(sql, timeout=timeout)
    if not result["success"]:
        return {"error": result["error"], "error_type": "mysql"}

    parsed = parse_tsv(result["stdout"])

    # Group by table
    tables = {}
    for row in parsed["rows"]:
        tname = row.get("TABLE_NAME", "")
        if tname not in tables:
            tables[tname] = []
        tables[tname].append({
            "column": row.get("COLUMN_NAME"),
            "type": row.get("DATA_TYPE"),
            "nullable": row.get("IS_NULLABLE"),
            "key": row.get("COLUMN_KEY"),
            "default": row.get("COLUMN_DEFAULT"),
            "extra": row.get("EXTRA"),
        })

    LOG.info("✅ Schema: %d tables, %d columns", len(tables), len(parsed["rows"]))
    return {
        "tables": tables,
        "table_count": len(tables),
        "column_count": len(parsed["rows"]),
    }


def count_rows(
    table: str,
    where: str = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    """Count rows in a table with optional WHERE."""
    valid, error = validate_table_name(table)
    if not valid:
        return {"error": error, "error_type": "validation"}

    if where:
        valid, error = validate_where_clause(where)
        if not valid:
            return {"error": error, "error_type": "validation"}

    sql = f"SELECT COUNT(*) as total FROM `{table}`"
    if where:
        sql += f" WHERE {where}"

    result = run_mysql_via_ssh(sql, timeout=timeout)
    if not result["success"]:
        return {"error": result["error"], "error_type": "mysql"}

    parsed = parse_tsv(result["stdout"])
    total = 0
    if parsed["rows"]:
        total = parsed["rows"][0].get("total", 0)

    LOG.info("✅ COUNT %s: %d rows", table, total)
    return {"table": table, "total": total, "where": where}
