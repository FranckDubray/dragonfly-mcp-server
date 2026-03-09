"""SQL validation — strict read-only enforcement."""
from __future__ import annotations
import re
from typing import Tuple

# Allowed SQL statement prefixes (read-only)
_READ_PREFIXES = ("select", "show", "describe", "explain", "with")

# Dangerous keywords that MUST NOT appear anywhere
_DANGEROUS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE"
    r"|RENAME|REPLACE|LOAD|CALL|SET|LOCK|UNLOCK|FLUSH)\b",
    re.IGNORECASE,
)

# Block comments that could hide mutations
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)


def validate_sql_read_only(sql: str) -> Tuple[bool, str]:
    """Validate that SQL is strictly read-only.

    Returns:
        (is_valid, error_message)
    """
    if not sql or not sql.strip():
        return False, "SQL query is empty"

    cleaned = sql.strip()

    # Remove block comments (could hide dangerous SQL)
    no_comments = _BLOCK_COMMENT.sub(" ", cleaned)

    # Check prefix
    lower = no_comments.lstrip().lower()
    if not any(lower.startswith(p) for p in _READ_PREFIXES):
        return False, (
            f"Read-only mode: query must start with "
            f"{', '.join(p.upper() for p in _READ_PREFIXES)}"
        )

    # Check for dangerous keywords
    match = _DANGEROUS.search(no_comments)
    if match:
        return False, (
            f"Read-only mode: forbidden keyword '{match.group()}' detected"
        )

    # Check for multiple statements (semicolons)
    # Allow trailing semicolon but block multiple statements
    parts = [p.strip() for p in cleaned.rstrip(";").split(";") if p.strip()]
    if len(parts) > 1:
        return False, "Read-only mode: multiple statements not allowed"

    # Size check
    if len(cleaned) > 10000:
        return False, "Query too large (max 10KB)"

    return True, ""


def validate_table_name(table: str) -> Tuple[bool, str]:
    """Validate table name (alphanumeric + underscore)."""
    if not table or not table.strip():
        return False, "Table name is required"
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", table.strip()):
        return False, f"Invalid table name: '{table}'"
    return True, ""


def validate_where_clause(where: str) -> Tuple[bool, str]:
    """Validate WHERE clause (no dangerous keywords)."""
    if not where:
        return True, ""
    match = _DANGEROUS.search(where)
    if match:
        return False, f"Forbidden keyword in WHERE: '{match.group()}'"
    return True, ""
