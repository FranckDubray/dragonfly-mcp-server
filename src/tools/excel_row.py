"""
Excel Row tool bootstrap (v2).
Exposes run() and spec() for MCP server.
"""
import logging
from ._excel_row import spec
from ._excel_row.api import execute_operation

logger = logging.getLogger(__name__)


def run(
    operation: str,
    file_path: str,
    sheet_name=None,
    position: int | None = None,
    row_data: dict | None = None,
    # New v2 formatting API
    row_format: dict | None = None,
    columns_format: dict | None = None,
    parse: dict | None = None,
    # Backwards-compat (deprecated)
    color: str | None = None,
    border_color: str | None = None,
    date_format: str | None = None,
    create_backup: bool = False,
    backup_version: int = 0,
    create_safety_backup: bool = True,
    **kwargs
):
    """
    Execute Excel row operation.

    Args:
        operation: insert_row | update_row | delete_row | list_backups | restore_backup
        file_path: Path to Excel file
        sheet_name: Sheet name (str) or index (int, 0-based)
        position: Row position (1-indexed, 1 = after header)
        row_data: dict (Excel or normalized column names)
        row_format: default row formatting
        columns_format: per-column formatting overrides
        parse: input parsing options (e.g., date_input_format)
        color, border_color, date_format: DEPRECATED compatibility
        create_backup: Create backup before modification
        backup_version, create_safety_backup: for restore_backup
    Returns:
        Operation result dict
    """
    try:
        return execute_operation(
            operation=operation,
            file_path=file_path,
            sheet_name=sheet_name,
            position=position,
            row_data=row_data,
            row_format=row_format,
            columns_format=columns_format,
            parse=parse,
            # legacy
            color=color,
            border_color=border_color,
            date_format=date_format,
            # backups
            create_backup_flag=create_backup,
            backup_version=backup_version,
            create_safety_backup=create_safety_backup,
        )
    except Exception as e:
        logger.error(f"Excel operation failed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": type(e).__name__,
            "message": str(e),
        }


__all__ = ["run", "spec"]
