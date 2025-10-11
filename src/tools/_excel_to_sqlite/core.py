"""
Core logic for excel_to_sqlite operations.
"""
from __future__ import annotations

import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from config import find_project_root
except Exception:
    find_project_root = lambda: Path.cwd()  # type: ignore

from . import excel_reader
from . import validators

logger = logging.getLogger(__name__)

PROJECT_ROOT = find_project_root()
SQLITE_DIR = PROJECT_ROOT / "sqlite3"


def import_excel_to_sqlite(
    excel_path: Path,
    db_name: str,
    sheet_name: str | int,
    table_name: str,
    if_exists: str = "replace",
    batch_size: int = 1000,
    skip_rows: int = 0,
    header_row: int = 0,
    column_mapping: Optional[Dict[str, str]] = None,
    type_mapping: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Import Excel data into SQLite database.
    
    Returns:
        {
            "success": bool,
            "db": str,
            "table": str,
            "rows_inserted": int,
            "columns": list[str],
            "duration_sec": float,
            "warnings": list[str]
        }
    """
    start_time = time.time()
    warnings = []
    
    # Check dependencies
    deps_ok, deps_err = excel_reader.check_dependencies()
    if not deps_ok:
        return {"error": deps_err}
    
    import pandas as pd
    
    logger.info(f"Starting import: {excel_path.name} -> {db_name}.{table_name}")
    
    # Read Excel data
    try:
        df = excel_reader.read_excel_data(
            excel_path,
            sheet_name,
            skip_rows=skip_rows,
            header_row=header_row
        )
    except Exception as e:
        return {"error": f"Failed to read Excel file: {e}"}
    
    if len(df) == 0:
        return {"error": "Excel sheet is empty"}
    
    # Prepare DataFrame for SQLite
    try:
        df, name_mapping = excel_reader.prepare_dataframe_for_sqlite(
            df,
            column_mapping=column_mapping,
            type_mapping=type_mapping
        )
    except Exception as e:
        return {"error": f"Failed to prepare data: {e}"}
    
    # Log column mapping
    if not column_mapping:
        logger.info(f"Auto-mapped columns: {name_mapping}")
        for orig, new in name_mapping.items():
            if orig != new:
                warnings.append(f"Column '{orig}' renamed to '{new}'")
    
    # Check for NULL values
    for col in df.columns:
        null_count = df[col].isna().sum()
        if null_count > 0:
            pct = (null_count / len(df)) * 100
            warnings.append(f"Column '{col}' contains {null_count} NULL values ({pct:.1f}%)")
    
    # Database path
    db_path = SQLITE_DIR / f"{db_name}.db"
    SQLITE_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing to database: {db_path}")
    
    # Write to SQLite using pandas
    try:
        conn = sqlite3.connect(str(db_path))
        
        # Write data in batches
        df.to_sql(
            table_name,
            conn,
            if_exists=if_exists,
            index=False,
            chunksize=batch_size
        )
        
        conn.close()
        
    except Exception as e:
        return {"error": f"Failed to write to SQLite: {e}"}
    
    duration = time.time() - start_time
    
    logger.info(f"Import completed: {len(df)} rows in {duration:.2f}s")
    
    return {
        "success": True,
        "db": f"{db_name}.db",
        "table": table_name,
        "rows_inserted": len(df),
        "columns": list(df.columns),
        "duration_sec": round(duration, 2),
        "warnings": warnings
    }


def preview_excel(
    excel_path: Path,
    sheet_name: str | int,
    max_rows: int = 10,
    skip_rows: int = 0,
    header_row: int = 0
) -> Dict[str, Any]:
    """
    Preview Excel data without importing.
    """
    # Check dependencies
    deps_ok, deps_err = excel_reader.check_dependencies()
    if not deps_ok:
        return {"error": deps_err}
    
    try:
        result = excel_reader.read_excel_preview(
            excel_path,
            sheet_name,
            max_rows=max_rows,
            skip_rows=skip_rows,
            header_row=header_row
        )
        return result
    except Exception as e:
        return {"error": f"Failed to preview Excel: {e}"}


def get_sheets(excel_path: Path) -> Dict[str, Any]:
    """
    Get list of sheets in Excel file.
    """
    # Check dependencies
    deps_ok, deps_err = excel_reader.check_dependencies()
    if not deps_ok:
        return {"error": deps_err}
    
    try:
        sheets = excel_reader.get_sheet_names(excel_path)
        return {
            "success": True,
            "file": excel_path.name,
            "sheets": sheets
        }
    except Exception as e:
        return {"error": f"Failed to read sheets: {e}"}


def get_info(excel_path: Path) -> Dict[str, Any]:
    """
    Get information about Excel file.
    """
    # Check dependencies
    deps_ok, deps_err = excel_reader.check_dependencies()
    if not deps_ok:
        return {"error": deps_err}
    
    try:
        info = excel_reader.get_excel_info(excel_path)
        return {
            "success": True,
            **info
        }
    except Exception as e:
        return {"error": f"Failed to get file info: {e}"}


def validate_mapping(
    excel_path: Path,
    sheet_name: str | int,
    db_name: str,
    table_name: str,
    column_mapping: Optional[Dict[str, str]] = None,
    skip_rows: int = 0,
    header_row: int = 0
) -> Dict[str, Any]:
    """
    Validate column mapping between Excel and SQLite.
    """
    # Check dependencies
    deps_ok, deps_err = excel_reader.check_dependencies()
    if not deps_ok:
        return {"error": deps_err}
    
    import pandas as pd
    
    # Read Excel columns
    try:
        df = excel_reader.read_excel_data(
            excel_path,
            sheet_name,
            skip_rows=skip_rows,
            header_row=header_row
        )
    except Exception as e:
        return {"error": f"Failed to read Excel: {e}"}
    
    excel_columns = list(df.columns)
    
    # Prepare column mapping
    if column_mapping:
        sqlite_columns = [column_mapping.get(col, col) for col in excel_columns]
        name_mapping = column_mapping
    else:
        # Auto-generate mapping
        df_prep, name_mapping = excel_reader.prepare_dataframe_for_sqlite(df)
        sqlite_columns = list(df_prep.columns)
    
    # Check if table exists in database
    db_path = SQLITE_DIR / f"{db_name}.db"
    table_exists = False
    db_table_schema = {}
    
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            if cursor.fetchone():
                table_exists = True
                
                # Get table schema
                cursor.execute(f"PRAGMA table_info({table_name})")
                for row in cursor.fetchall():
                    col_name = row[1]
                    col_type = row[2]
                    db_table_schema[col_name] = col_type
            
            conn.close()
        except Exception as e:
            logger.warning(f"Could not check database: {e}")
    
    # Validate mapping
    mapping_details = {}
    errors = []
    warnings = []
    
    for excel_col, sqlite_col in name_mapping.items():
        # Detect Excel type
        excel_type = excel_reader.detect_column_type(df[excel_col])
        
        # Get SQLite type if table exists
        sqlite_type = db_table_schema.get(sqlite_col, "N/A")
        
        # Check compatibility
        compatible = True
        if table_exists and sqlite_col in db_table_schema:
            # Basic compatibility check
            if excel_type == "INTEGER" and sqlite_type not in ["INTEGER", "REAL"]:
                compatible = False
                errors.append(f"Column '{sqlite_col}': type mismatch (Excel: {excel_type}, SQLite: {sqlite_type})")
            elif excel_type == "REAL" and sqlite_type not in ["REAL", "INTEGER"]:
                compatible = False
                errors.append(f"Column '{sqlite_col}': type mismatch (Excel: {excel_type}, SQLite: {sqlite_type})")
        
        mapping_details[excel_col] = {
            "sqlite": sqlite_col,
            "type_excel": excel_type,
            "type_sqlite": sqlite_type if table_exists else "AUTO",
            "compatible": compatible
        }
    
    # Check for columns in SQLite table not in Excel
    if table_exists:
        for db_col in db_table_schema:
            if db_col not in sqlite_columns:
                warnings.append(f"SQLite column '{db_col}' not present in Excel data")
    
    return {
        "success": True,
        "valid": len(errors) == 0,
        "table_exists": table_exists,
        "excel_columns": excel_columns,
        "sqlite_columns": sqlite_columns,
        "mapping": mapping_details,
        "warnings": warnings,
        "errors": errors
    }
