"""
Excel reader using Pandas.
Handles reading Excel files, detecting types, and preparing data for SQLite.
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import pandas as pd
    import openpyxl
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

logger = logging.getLogger(__name__)


def check_dependencies() -> Tuple[bool, Optional[str]]:
    """Check if required dependencies are available."""
    if not PANDAS_AVAILABLE:
        return False, "pandas and openpyxl are required. Install with: pip install pandas openpyxl"
    return True, None


def _serialize_value(val: Any) -> Any:
    """Convert pandas types to JSON-serializable types."""
    if pd.isna(val):
        return None
    if isinstance(val, pd.Timestamp):
        return val.isoformat()
    if isinstance(val, (pd.Int64Dtype, pd.Int32Dtype, pd.Int16Dtype, pd.Int8Dtype)):
        return int(val)
    if hasattr(val, 'item'):  # numpy types
        return val.item()
    return val


def get_excel_info(excel_path: Path) -> Dict[str, Any]:
    """
    Get information about Excel file without reading data.
    
    Returns:
        {
            "file": str,
            "size_bytes": int,
            "size_human": str,
            "sheets_count": int,
            "sheets": [{"name": str, "rows": int, "columns": int}, ...],
            "created": str (ISO format),
            "modified": str (ISO format)
        }
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas is required")
    
    # File metadata
    stat = excel_path.stat()
    size_bytes = stat.st_size
    size_mb = size_bytes / (1024 * 1024)
    size_human = f"{size_mb:.1f} MB" if size_mb >= 1 else f"{size_bytes / 1024:.1f} KB"
    
    created = datetime.fromtimestamp(stat.st_ctime).isoformat()
    modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
    
    # Read Excel file to get sheet info
    excel_file = pd.ExcelFile(excel_path)
    sheets = []
    
    for sheet_name in excel_file.sheet_names:
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name, nrows=0)
            rows = pd.read_excel(excel_path, sheet_name=sheet_name).shape[0]
            columns = len(df.columns)
            sheets.append({
                "name": sheet_name,
                "rows": rows,
                "columns": columns
            })
        except Exception as e:
            logger.warning(f"Could not read sheet '{sheet_name}': {e}")
            sheets.append({
                "name": sheet_name,
                "rows": 0,
                "columns": 0
            })
    
    return {
        "file": excel_path.name,
        "size_bytes": size_bytes,
        "size_human": size_human,
        "sheets_count": len(sheets),
        "sheets": sheets,
        "created": created,
        "modified": modified
    }


def get_sheet_names(excel_path: Path) -> List[Dict[str, Any]]:
    """
    Get list of sheets in Excel file.
    
    Returns:
        [{"index": int, "name": str, "rows": int}, ...]
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas is required")
    
    excel_file = pd.ExcelFile(excel_path)
    sheets = []
    
    for idx, sheet_name in enumerate(excel_file.sheet_names):
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            rows = len(df)
        except Exception:
            rows = 0
        
        sheets.append({
            "index": idx,
            "name": sheet_name,
            "rows": rows
        })
    
    return sheets


def read_excel_preview(
    excel_path: Path,
    sheet_name: str | int,
    max_rows: int = 10,
    skip_rows: int = 0,
    header_row: int = 0
) -> Dict[str, Any]:
    """
    Read preview of Excel data with type detection.
    
    Returns:
        {
            "success": bool,
            "file": str,
            "sheet": str,
            "total_rows": int,
            "columns": {
                "col_name": {
                    "type": str,  # "TEXT", "INTEGER", "REAL", "DATETIME", "BOOLEAN"
                    "sample": Any,
                    "nulls": int
                }
            },
            "preview_rows": [dict, ...]
        }
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas is required")
    
    logger.info(f"Reading preview from '{excel_path.name}', sheet '{sheet_name}'")
    
    # Read full dataframe to get total rows
    df_full = pd.read_excel(
        excel_path,
        sheet_name=sheet_name,
        skiprows=skip_rows,
        header=header_row
    )
    total_rows = len(df_full)
    
    # Read preview
    df = df_full.head(max_rows)
    
    # Analyze columns
    columns = {}
    for col in df.columns:
        col_data = df[col]
        null_count = col_data.isna().sum()
        
        # Detect type
        dtype = detect_column_type(col_data)
        
        # Get sample value (first non-null)
        sample = None
        for val in col_data:
            if pd.notna(val):
                sample = _serialize_value(val)
                break
        
        columns[str(col)] = {
            "type": dtype,
            "sample": sample,
            "nulls": int(null_count)
        }
    
    # Convert preview to list of dicts with serialized values
    preview_rows = []
    for _, row in df.iterrows():
        row_dict = {}
        for col, val in row.items():
            row_dict[str(col)] = _serialize_value(val)
        preview_rows.append(row_dict)
    
    # Get actual sheet name (if index was provided)
    actual_sheet = sheet_name
    if isinstance(sheet_name, int):
        excel_file = pd.ExcelFile(excel_path)
        actual_sheet = excel_file.sheet_names[sheet_name]
    
    return {
        "success": True,
        "file": excel_path.name,
        "sheet": str(actual_sheet),
        "total_rows": total_rows,
        "columns": columns,
        "preview_rows": preview_rows
    }


def read_excel_data(
    excel_path: Path,
    sheet_name: str | int,
    skip_rows: int = 0,
    header_row: int = 0
) -> pd.DataFrame:
    """
    Read Excel data into pandas DataFrame.
    
    Args:
        excel_path: Path to Excel file
        sheet_name: Sheet name or index
        skip_rows: Number of rows to skip at beginning
        header_row: Row index for column headers
    
    Returns:
        pandas DataFrame
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas is required")
    
    logger.info(f"Reading data from '{excel_path.name}', sheet '{sheet_name}'")
    
    df = pd.read_excel(
        excel_path,
        sheet_name=sheet_name,
        skiprows=skip_rows,
        header=header_row
    )
    
    logger.info(f"Read {len(df)} rows, {len(df.columns)} columns")
    
    return df


def detect_column_type(series: pd.Series) -> str:
    """
    Detect SQLite type for pandas Series.
    
    Returns:
        "INTEGER" | "REAL" | "TEXT" | "DATETIME" | "BOOLEAN"
    """
    # Drop NaN values for type detection
    series_clean = series.dropna()
    
    if len(series_clean) == 0:
        return "TEXT"
    
    # Check pandas dtype
    dtype = series.dtype
    
    # Boolean
    if dtype == bool or series_clean.isin([True, False, 0, 1]).all():
        return "BOOLEAN"
    
    # Integer
    if pd.api.types.is_integer_dtype(dtype):
        return "INTEGER"
    
    # Float
    if pd.api.types.is_float_dtype(dtype):
        # Check if all values are actually integers
        if (series_clean % 1 == 0).all():
            return "INTEGER"
        return "REAL"
    
    # Datetime
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "DATETIME"
    
    # Try to detect datetime from string
    if pd.api.types.is_string_dtype(dtype):
        try:
            pd.to_datetime(series_clean.head(10), errors='raise')
            return "DATETIME"
        except Exception:
            pass
    
    # Default to TEXT
    return "TEXT"


def prepare_dataframe_for_sqlite(
    df: pd.DataFrame,
    column_mapping: Optional[Dict[str, str]] = None,
    type_mapping: Optional[Dict[str, str]] = None
) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Prepare DataFrame for SQLite insertion.
    
    - Apply column mapping (or auto-sanitize)
    - Apply type conversions
    - Handle NaN/NULL values
    
    Returns:
        (prepared_df, column_name_mapping)
    """
    df = df.copy()
    
    # Column name mapping
    if column_mapping:
        # Use provided mapping
        df = df.rename(columns=column_mapping)
        name_mapping = column_mapping
    else:
        # Auto-sanitize column names
        from .validators import sanitize_column_name, ensure_unique_column_names
        
        original_names = list(df.columns)
        sanitized = [sanitize_column_name(str(col)) for col in original_names]
        sanitized = ensure_unique_column_names(sanitized)
        
        name_mapping = dict(zip(original_names, sanitized))
        df = df.rename(columns=name_mapping)
    
    # Type conversions
    if type_mapping:
        for col, sqlite_type in type_mapping.items():
            if col not in df.columns:
                logger.warning(f"Column '{col}' not found in DataFrame, skipping type mapping")
                continue
            
            try:
                if sqlite_type == "INTEGER":
                    df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
                elif sqlite_type == "REAL":
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                elif sqlite_type == "TEXT":
                    df[col] = df[col].astype(str)
                elif sqlite_type == "DATETIME":
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            except Exception as e:
                logger.warning(f"Could not convert column '{col}' to {sqlite_type}: {e}")
    
    # Convert datetime to ISO8601 strings for SQLite
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Convert boolean to integer (0/1)
    for col in df.columns:
        if df[col].dtype == bool:
            df[col] = df[col].astype(int)
    
    return df, name_mapping
