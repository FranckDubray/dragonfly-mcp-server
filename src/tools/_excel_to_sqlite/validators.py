"""
Validators for excel_to_sqlite tool.
Pure validation functions with no side effects.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    from config import find_project_root
except Exception:
    find_project_root = lambda: Path.cwd()  # type: ignore


PROJECT_ROOT = find_project_root()
SQLITE_DIR = PROJECT_ROOT / "sqlite3"

# Valid SQLite types
VALID_SQLITE_TYPES = {"INTEGER", "REAL", "TEXT", "BLOB"}

# Valid column name pattern (SQLite compatible)
COLUMN_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def validate_excel_path(excel_path: str) -> Tuple[bool, Optional[str], Optional[Path]]:
    """
    Validate Excel file path.
    
    Returns:
        (is_valid, error_message, resolved_path)
    """
    if not excel_path or not isinstance(excel_path, str):
        return False, "excel_path must be a non-empty string", None
    
    # Check extension
    if not excel_path.lower().endswith(".xlsx"):
        return False, "Only .xlsx files are supported", None
    
    # Resolve path relative to project root
    try:
        path = (PROJECT_ROOT / excel_path).resolve()
    except Exception as e:
        return False, f"Invalid path: {e}", None
    
    # Security: ensure path is within project root (no path traversal)
    try:
        path.relative_to(PROJECT_ROOT)
    except ValueError:
        return False, "Path must be within project root (no path traversal)", None
    
    # Check file exists
    if not path.exists():
        return False, f"File not found: {excel_path}", None
    
    if not path.is_file():
        return False, f"Path is not a file: {excel_path}", None
    
    return True, None, path


def validate_db_name(db_name: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate database name.
    
    Returns:
        (is_valid, error_message, normalized_name)
    """
    if not db_name or not isinstance(db_name, str):
        return False, "db_name must be a non-empty string", None
    
    db_name = db_name.strip()
    
    # Remove .db extension if present
    if db_name.endswith(".db"):
        db_name = db_name[:-3]
    
    # Check valid characters (alphanumeric, underscore, hyphen)
    if not re.match(r"^[A-Za-z0-9_-]+$", db_name):
        return False, "db_name can only contain letters, digits, underscore, and hyphen", None
    
    return True, None, db_name


def validate_table_name(table_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate SQLite table name.
    
    Returns:
        (is_valid, error_message)
    """
    if not table_name or not isinstance(table_name, str):
        return False, "table_name must be a non-empty string"
    
    table_name = table_name.strip()
    
    # SQLite table names: alphanumeric + underscore, cannot start with digit
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
        return False, "Invalid table name (must start with letter/underscore, alphanumeric + underscore only)"
    
    # Reserved keywords check (basic list)
    reserved = {
        "select", "insert", "update", "delete", "create", "drop", "alter",
        "table", "index", "view", "trigger", "from", "where", "order", "group"
    }
    if table_name.lower() in reserved:
        return False, f"Table name '{table_name}' is a reserved SQL keyword"
    
    return True, None


def validate_sheet_name(sheet_name: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate sheet name (string or integer index).
    
    Returns:
        (is_valid, error_message)
    """
    if sheet_name is None:
        return False, "sheet_name is required"
    
    if isinstance(sheet_name, str):
        if not sheet_name.strip():
            return False, "sheet_name cannot be empty"
        return True, None
    
    if isinstance(sheet_name, int):
        if sheet_name < 0:
            return False, "sheet_name index must be >= 0"
        return True, None
    
    return False, "sheet_name must be string or integer"


def validate_column_mapping(column_mapping: Optional[Dict[str, str]]) -> Tuple[bool, Optional[str]]:
    """
    Validate column mapping dictionary.
    
    Returns:
        (is_valid, error_message)
    """
    if column_mapping is None:
        return True, None
    
    if not isinstance(column_mapping, dict):
        return False, "column_mapping must be a dictionary"
    
    for excel_col, sqlite_col in column_mapping.items():
        if not isinstance(excel_col, str) or not isinstance(sqlite_col, str):
            return False, "column_mapping keys and values must be strings"
        
        if not excel_col.strip() or not sqlite_col.strip():
            return False, "column_mapping keys and values cannot be empty"
    
    return True, None


def validate_type_mapping(type_mapping: Optional[Dict[str, str]]) -> Tuple[bool, Optional[str]]:
    """
    Validate type mapping dictionary.
    
    Returns:
        (is_valid, error_message)
    """
    if type_mapping is None:
        return True, None
    
    if not isinstance(type_mapping, dict):
        return False, "type_mapping must be a dictionary"
    
    for col, dtype in type_mapping.items():
        if not isinstance(col, str) or not isinstance(dtype, str):
            return False, "type_mapping keys and values must be strings"
        
        if dtype.upper() not in VALID_SQLITE_TYPES:
            return False, f"Invalid SQLite type '{dtype}' (valid: {', '.join(VALID_SQLITE_TYPES)})"
    
    return True, None


def validate_if_exists(if_exists: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate if_exists parameter.
    
    Returns:
        (is_valid, error_message)
    """
    if if_exists is None:
        return True, None
    
    if not isinstance(if_exists, str):
        return False, "if_exists must be a string"
    
    if if_exists not in ["replace", "append", "fail"]:
        return False, "if_exists must be one of: replace, append, fail"
    
    return True, None


def validate_batch_size(batch_size: Optional[int]) -> Tuple[bool, Optional[str], int]:
    """
    Validate batch size.
    
    Returns:
        (is_valid, error_message, normalized_value)
    """
    default = 1000
    
    if batch_size is None:
        return True, None, default
    
    if not isinstance(batch_size, int):
        return False, "batch_size must be an integer", default
    
    if batch_size < 100 or batch_size > 10000:
        return False, "batch_size must be between 100 and 10000", default
    
    return True, None, batch_size


def sanitize_column_name(name: str) -> str:
    """
    Sanitize Excel column name for SQLite.
    
    Rules:
    - Convert to lowercase
    - Replace spaces with underscores
    - Remove special characters (keep only alphanumeric + underscore)
    - Ensure starts with letter or underscore
    - Add prefix if starts with digit
    
    Examples:
        "Nom Client" -> "nom_client"
        "Date-Commande" -> "date_commande"
        "Prix (€)" -> "prix"
        "2023 Sales" -> "col_2023_sales"
    """
    # Convert to lowercase
    name = name.lower()
    
    # Replace spaces and hyphens with underscores
    name = name.replace(" ", "_").replace("-", "_")
    
    # Remove special characters (keep only alphanumeric + underscore)
    name = re.sub(r"[^a-z0-9_]", "", name)
    
    # Ensure not empty
    if not name:
        name = "column"
    
    # Ensure starts with letter or underscore
    if name[0].isdigit():
        name = "col_" + name
    
    return name


def ensure_unique_column_names(names: list[str]) -> list[str]:
    """
    Ensure all column names are unique by adding suffixes.
    
    Examples:
        ["name", "name", "age"] -> ["name", "name_1", "age"]
        ["id", "id", "id"] -> ["id", "id_1", "id_2"]
    """
    seen = {}
    result = []
    
    for name in names:
        original = name
        counter = 0
        
        while name in seen:
            counter += 1
            name = f"{original}_{counter}"
        
        seen[name] = True
        result.append(name)
    
    return result
