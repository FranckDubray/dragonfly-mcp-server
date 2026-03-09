"""API routing layer for Portal DB."""
from __future__ import annotations
from typing import Dict, Any

from .core import (
    execute_query,
    list_tables,
    describe_table,
    get_schema,
    count_rows,
)


def route_operation(operation: str, **params) -> Dict[str, Any]:
    """Route portal_db operation to the appropriate handler.

    Args:
        operation: Operation type
        **params: Operation parameters

    Returns:
        Operation result or error dict
    """
    try:
        if operation == "query":
            sql = params.get("sql")
            if not sql:
                return {"error": "Parameter 'sql' is required for query"}
            return execute_query(
                sql=sql,
                limit=params.get("limit", 50),
                offset=params.get("offset", 0),
                timeout=params.get("timeout", 30),
            )

        elif operation == "tables":
            return list_tables(timeout=params.get("timeout", 30))

        elif operation == "describe":
            table = params.get("table")
            if not table:
                return {"error": "Parameter 'table' is required for describe"}
            return describe_table(
                table=table,
                timeout=params.get("timeout", 30),
            )

        elif operation == "schema":
            return get_schema(timeout=params.get("timeout", 60))

        elif operation == "count":
            table = params.get("table")
            if not table:
                return {"error": "Parameter 'table' is required for count"}
            return count_rows(
                table=table,
                where=params.get("where"),
                timeout=params.get("timeout", 30),
            )

        else:
            return {"error": f"Unknown operation: {operation}"}

    except Exception as e:
        return {"error": f"Operation failed: {str(e)}", "error_type": "unknown"}
