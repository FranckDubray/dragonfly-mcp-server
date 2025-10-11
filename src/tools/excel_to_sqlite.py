"""
Excel to SQLite Tool - Import Excel data into SQLite databases.

Imports Excel (.xlsx) files into SQLite databases with automatic schema detection,
column name sanitization, type mapping, and batch processing.

Operations:
- import_excel: Import complete Excel sheet into SQLite table
- preview: Preview data with type detection (no insertion)
- get_sheets: List all sheets in Excel file
- get_info: Get file metadata and sheet information
- validate_mapping: Validate column mapping before import

Dependencies:
- pandas (for Excel reading and data manipulation)
- openpyxl (Excel file engine)

Install with: pip install pandas openpyxl
"""
from __future__ import annotations

from typing import Any, Dict

from ._excel_to_sqlite.api import route_operation
from ._excel_to_sqlite import spec as _spec


def run(operation: str = None, **params) -> Dict[str, Any]:
    """
    Execute excel_to_sqlite operation.
    
    Args:
        operation: Operation name (import_excel, preview, get_sheets, get_info, validate_mapping)
        **params: Operation-specific parameters
    
    Returns:
        Result dictionary with success/error status
    """
    # Get operation from params if not provided as arg
    if operation is None:
        operation = params.get("operation")
    
    if not operation:
        return {
            "error": "Parameter 'operation' is required",
            "available_operations": [
                "import_excel",
                "preview",
                "get_sheets",
                "get_info",
                "validate_mapping"
            ]
        }
    
    # Route to appropriate handler
    return route_operation(operation, **params)


def spec() -> Dict[str, Any]:
    """Return tool specification."""
    return _spec()
