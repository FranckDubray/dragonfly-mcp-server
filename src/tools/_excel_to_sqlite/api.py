"""
API routing for excel_to_sqlite operations.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from . import core
from . import validators

logger = logging.getLogger(__name__)


def route_operation(operation: str, **params) -> Dict[str, Any]:
    """
    Route operation to appropriate handler.
    
    Args:
        operation: Operation name
        **params: Operation parameters
    
    Returns:
        Result dictionary
    """
    operation = operation.lower().strip()
    
    logger.info(f"excel_to_sqlite operation: {operation}")
    
    if operation == "import_excel":
        return handle_import_excel(**params)
    
    elif operation == "preview":
        return handle_preview(**params)
    
    elif operation == "get_sheets":
        return handle_get_sheets(**params)
    
    elif operation == "get_info":
        return handle_get_info(**params)
    
    elif operation == "validate_mapping":
        return handle_validate_mapping(**params)
    
    else:
        return {"error": f"Unknown operation: {operation}"}


def handle_import_excel(**params) -> Dict[str, Any]:
    """
    Handle import_excel operation.
    
    Required params: excel_path, db_name, sheet_name, table_name
    Optional: if_exists, batch_size, skip_rows, header_row, column_mapping, type_mapping
    """
    # Validate required parameters
    excel_path = params.get("excel_path")
    db_name = params.get("db_name")
    sheet_name = params.get("sheet_name")
    table_name = params.get("table_name")
    
    if not excel_path:
        return {"error": "Parameter 'excel_path' is required"}
    if not db_name:
        return {"error": "Parameter 'db_name' is required"}
    if sheet_name is None:
        return {"error": "Parameter 'sheet_name' is required"}
    if not table_name:
        return {"error": "Parameter 'table_name' is required"}
    
    # Validate excel_path
    valid, error, resolved_path = validators.validate_excel_path(excel_path)
    if not valid:
        return {"error": error}
    
    # Validate db_name
    valid, error, normalized_db = validators.validate_db_name(db_name)
    if not valid:
        return {"error": error}
    
    # Validate sheet_name
    valid, error = validators.validate_sheet_name(sheet_name)
    if not valid:
        return {"error": error}
    
    # Validate table_name
    valid, error = validators.validate_table_name(table_name)
    if not valid:
        return {"error": error}
    
    # Validate optional parameters
    if_exists = params.get("if_exists", "replace")
    valid, error = validators.validate_if_exists(if_exists)
    if not valid:
        return {"error": error}
    
    batch_size = params.get("batch_size")
    valid, error, batch_size = validators.validate_batch_size(batch_size)
    if not valid:
        return {"error": error}
    
    column_mapping = params.get("column_mapping")
    valid, error = validators.validate_column_mapping(column_mapping)
    if not valid:
        return {"error": error}
    
    type_mapping = params.get("type_mapping")
    valid, error = validators.validate_type_mapping(type_mapping)
    if not valid:
        return {"error": error}
    
    skip_rows = params.get("skip_rows", 0)
    if not isinstance(skip_rows, int) or skip_rows < 0:
        return {"error": "skip_rows must be a non-negative integer"}
    
    header_row = params.get("header_row", 0)
    if not isinstance(header_row, int) or header_row < 0:
        return {"error": "header_row must be a non-negative integer"}
    
    # Execute import
    return core.import_excel_to_sqlite(
        excel_path=resolved_path,
        db_name=normalized_db,
        sheet_name=sheet_name,
        table_name=table_name,
        if_exists=if_exists,
        batch_size=batch_size,
        skip_rows=skip_rows,
        header_row=header_row,
        column_mapping=column_mapping,
        type_mapping=type_mapping
    )


def handle_preview(**params) -> Dict[str, Any]:
    """
    Handle preview operation.
    
    Required params: excel_path, sheet_name
    Optional: max_rows, skip_rows, header_row
    """
    excel_path = params.get("excel_path")
    sheet_name = params.get("sheet_name")
    
    if not excel_path:
        return {"error": "Parameter 'excel_path' is required"}
    if sheet_name is None:
        return {"error": "Parameter 'sheet_name' is required"}
    
    # Validate excel_path
    valid, error, resolved_path = validators.validate_excel_path(excel_path)
    if not valid:
        return {"error": error}
    
    # Validate sheet_name
    valid, error = validators.validate_sheet_name(sheet_name)
    if not valid:
        return {"error": error}
    
    max_rows = params.get("max_rows", 10)
    if not isinstance(max_rows, int) or max_rows < 1 or max_rows > 100:
        return {"error": "max_rows must be between 1 and 100"}
    
    skip_rows = params.get("skip_rows", 0)
    if not isinstance(skip_rows, int) or skip_rows < 0:
        return {"error": "skip_rows must be a non-negative integer"}
    
    header_row = params.get("header_row", 0)
    if not isinstance(header_row, int) or header_row < 0:
        return {"error": "header_row must be a non-negative integer"}
    
    return core.preview_excel(
        excel_path=resolved_path,
        sheet_name=sheet_name,
        max_rows=max_rows,
        skip_rows=skip_rows,
        header_row=header_row
    )


def handle_get_sheets(**params) -> Dict[str, Any]:
    """
    Handle get_sheets operation.
    
    Required params: excel_path
    """
    excel_path = params.get("excel_path")
    
    if not excel_path:
        return {"error": "Parameter 'excel_path' is required"}
    
    # Validate excel_path
    valid, error, resolved_path = validators.validate_excel_path(excel_path)
    if not valid:
        return {"error": error}
    
    return core.get_sheets(excel_path=resolved_path)


def handle_get_info(**params) -> Dict[str, Any]:
    """
    Handle get_info operation.
    
    Required params: excel_path
    """
    excel_path = params.get("excel_path")
    
    if not excel_path:
        return {"error": "Parameter 'excel_path' is required"}
    
    # Validate excel_path
    valid, error, resolved_path = validators.validate_excel_path(excel_path)
    if not valid:
        return {"error": error}
    
    return core.get_info(excel_path=resolved_path)


def handle_validate_mapping(**params) -> Dict[str, Any]:
    """
    Handle validate_mapping operation.
    
    Required params: excel_path, sheet_name, db_name, table_name
    Optional: column_mapping, skip_rows, header_row
    """
    excel_path = params.get("excel_path")
    sheet_name = params.get("sheet_name")
    db_name = params.get("db_name")
    table_name = params.get("table_name")
    
    if not excel_path:
        return {"error": "Parameter 'excel_path' is required"}
    if sheet_name is None:
        return {"error": "Parameter 'sheet_name' is required"}
    if not db_name:
        return {"error": "Parameter 'db_name' is required"}
    if not table_name:
        return {"error": "Parameter 'table_name' is required"}
    
    # Validate excel_path
    valid, error, resolved_path = validators.validate_excel_path(excel_path)
    if not valid:
        return {"error": error}
    
    # Validate db_name
    valid, error, normalized_db = validators.validate_db_name(db_name)
    if not valid:
        return {"error": error}
    
    # Validate sheet_name
    valid, error = validators.validate_sheet_name(sheet_name)
    if not valid:
        return {"error": error}
    
    # Validate table_name
    valid, error = validators.validate_table_name(table_name)
    if not valid:
        return {"error": error}
    
    column_mapping = params.get("column_mapping")
    valid, error = validators.validate_column_mapping(column_mapping)
    if not valid:
        return {"error": error}
    
    skip_rows = params.get("skip_rows", 0)
    if not isinstance(skip_rows, int) or skip_rows < 0:
        return {"error": "skip_rows must be a non-negative integer"}
    
    header_row = params.get("header_row", 0)
    if not isinstance(header_row, int) or header_row < 0:
        return {"error": "header_row must be a non-negative integer"}
    
    return core.validate_mapping(
        excel_path=resolved_path,
        sheet_name=sheet_name,
        db_name=normalized_db,
        table_name=table_name,
        column_mapping=column_mapping,
        skip_rows=skip_rows,
        header_row=header_row
    )
