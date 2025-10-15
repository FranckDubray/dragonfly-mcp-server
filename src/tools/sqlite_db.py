"""
SQLite3 Tool - Manage lightweight databases under a dedicated project folder.

Base directory: <PROJECT_ROOT>/sqlite3
- No external dependency (uses Python stdlib sqlite3)

Operations:
- create_db(name, schema?) -> create an empty DB (or initialize with SQL script)
- list_dbs() -> list available .db files
- delete_db(name) -> delete a database file
- get_tables(db) -> list tables
- describe(db, table) -> columns for a table
- execute(db, query, params?, many?, return_rows?, limit?) -> run SQL and return rows/metrics
- executescript(db, script) -> run multiple statements in one call

Notes:
- The parameter "db" and "name" refer to the logical DB name (with or without .db).
- DB files are created in <PROJECT_ROOT>/sqlite3 and paths are sanitized (alnum, _ and -).
- LIMIT parameter (default: 100, max: 1000): For SELECT queries, automatically truncates results
  to avoid massive outputs. Add explicit LIMIT clause in your query for precise control.
- Case-insensitive matching: "alain" will match both "worker_alain.db" and "worker_Alain.db"
"""
from __future__ import annotations

import os
import re
import sqlite3
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
import json

try:
    from config import find_project_root
except Exception:
    find_project_root = lambda: Path.cwd()  # type: ignore

PROJECT_ROOT = find_project_root()
BASE_DIR = PROJECT_ROOT / "sqlite3"
BASE_DIR.mkdir(parents=True, exist_ok=True)
_SPEC_DIR = Path(__file__).resolve().parent.parent / "tool_specs"

_DB_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+(\.db)?$")

# Logging setup
logger = logging.getLogger(__name__)


def _load_spec_json(name: str) -> Dict[str, Any]:
    """Load and return the canonical JSON spec (source of truth)."""
    p = _SPEC_DIR / f"{name}.json"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _normalize_name(name: str) -> str:
    name = name.strip()
    if not name:
        raise ValueError("empty database name")
    if not _DB_NAME_RE.match(name):
        raise ValueError("invalid database name (allowed: letters, digits, _ , -, optional .db)")
    if not name.endswith(".db"):
        name = name + ".db"
    return name


def _db_path(name: str, must_exist: bool = False) -> Path:
    """
    Resolve database path with case-insensitive matching.
    
    Args:
        name: Database name (with or without .db, with or without worker_ prefix)
        must_exist: If True, raises FileNotFoundError if not found
        
    Returns:
        Path to the database file
        
    Raises:
        FileNotFoundError: If must_exist=True and no matching file found
        ValueError: If name is invalid
    """
    norm = _normalize_name(name)
    
    # Try exact match first
    exact_path = (BASE_DIR / norm).resolve()
    if exact_path.exists():
        return exact_path
    
    # If name starts with "worker_", try case variations
    if norm.startswith("worker_"):
        # Extract the worker name part (after "worker_")
        worker_part = norm[7:-3]  # Remove "worker_" prefix and ".db" suffix
        
        # Try variations: original, lowercase, capitalize
        variations = [
            f"worker_{worker_part}.db",
            f"worker_{worker_part.lower()}.db",
            f"worker_{worker_part.capitalize()}.db",
            f"worker_{worker_part.upper()}.db"
        ]
        
        for variant in variations:
            test_path = (BASE_DIR / variant).resolve()
            if test_path.exists():
                logger.info(f"📁 Matched '{name}' → '{variant}' (case-insensitive)")
                return test_path
    
    # If not found and must_exist, raise error
    if must_exist:
        raise FileNotFoundError(f"Database '{name}' not found in {BASE_DIR}")
    
    # Otherwise return the normalized path (for create operations)
    return exact_path


def _row_factory(cursor: sqlite3.Cursor, row: Tuple[Any, ...]) -> Dict[str, Any]:
    return {col[0]: row[i] for i, col in enumerate(cursor.description or [])}


def _is_select_like(sql: str) -> bool:
    s = sql.lstrip().lower()
    return s.startswith("select") or s.startswith("pragma") or s.startswith("with")


def _ensure_dir() -> Dict[str, Any]:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    return {"base_dir": str(BASE_DIR)}


def run(operation: str, **params) -> Dict[str, Any]:
    op = (operation or "").lower().strip()

    if op == "ensure_dir":
        return {**_ensure_dir()}

    if op == "list_dbs":
        _ensure_dir()
        items = sorted([p.name for p in BASE_DIR.glob("*.db") if p.is_file()])
        return {"base_dir": str(BASE_DIR), "databases": items, "count": len(items)}

    if op == "create_db":
        name = params.get("name")
        schema = params.get("schema")  # optional SQL script
        if not isinstance(name, str) or not name.strip():
            logger.warning("create_db: missing or invalid 'name' parameter")
            return {"error": "name is required (string)"}
        try:
            path = _db_path(name, must_exist=False)
        except Exception as e:
            logger.warning(f"create_db: invalid name '{name}': {e}")
            return {"error": str(e)}
        _ensure_dir()
        try:
            must_init = not path.exists()
            conn = sqlite3.connect(str(path))
            try:
                if schema and isinstance(schema, str):
                    if len(schema) > 51200:
                        logger.warning(f"create_db: schema too large ({len(schema)} bytes, max 50KB)")
                        return {"error": "schema exceeds 50KB limit"}
                    conn.executescript(schema)
                    conn.commit()
            finally:
                conn.close()
            logger.info(f"create_db: {'created' if must_init else 'opened'} {path.name}")
            return {"db": path.name, "path": str(path), "created": must_init}
        except Exception as e:
            logger.error(f"create_db failed for '{name}': {e}")
            return {"error": f"create_db failed: {e}"}

    if op == "delete_db":
        name = params.get("name")
        if not isinstance(name, str) or not name.strip():
            logger.warning("delete_db: missing or invalid 'name' parameter")
            return {"error": "name is required (string)"}
        try:
            path = _db_path(name, must_exist=True)
        except FileNotFoundError as e:
            logger.warning(f"delete_db: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.warning(f"delete_db: invalid name '{name}': {e}")
            return {"error": str(e)}
        try:
            path.unlink()
            logger.info(f"delete_db: deleted {path.name}")
            return {"deleted": path.name}
        except Exception as e:
            logger.error(f"delete_db failed for '{path.name}': {e}")
            return {"error": f"delete_db failed: {e}"}

    if op == "get_tables":
        db = params.get("db")
        if not isinstance(db, str) or not db.strip():
            logger.warning("get_tables: missing or invalid 'db' parameter")
            return {"error": "db is required (string)"}
        try:
            path = _db_path(db, must_exist=True)
        except FileNotFoundError as e:
            logger.warning(f"get_tables: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.warning(f"get_tables: invalid db '{db}': {e}")
            return {"error": str(e)}
        try:
            conn = sqlite3.connect(str(path))
            conn.row_factory = _row_factory
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            rows = cur.fetchall()
            cur.close(); conn.close()
            tables = [r.get("name") for r in rows]
            logger.info(f"get_tables: {len(tables)} tables in {path.name}")
            return {"db": path.name, "tables": tables, "count": len(tables)}
        except Exception as e:
            logger.error(f"get_tables failed for '{path.name}': {e}")
            return {"error": f"get_tables failed: {e}"}

    if op == "describe":
        db = params.get("db"); table = params.get("table")
        if not isinstance(db, str) or not db.strip():
            logger.warning("describe: missing or invalid 'db' parameter")
            return {"error": "db is required (string)"}
        if not isinstance(table, str) or not table.strip():
            logger.warning("describe: missing or invalid 'table' parameter")
            return {"error": "table is required (string)"}
        try:
            path = _db_path(db, must_exist=True)
        except FileNotFoundError as e:
            logger.warning(f"describe: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.warning(f"describe: invalid db '{db}': {e}")
            return {"error": str(e)}
        try:
            conn = sqlite3.connect(str(path))
            conn.row_factory = _row_factory
            cur = conn.cursor()
            cur.execute(f"PRAGMA table_info({table})")
            rows = cur.fetchall()
            cur.close(); conn.close()
            logger.info(f"describe: {len(rows)} columns in {table} ({path.name})")
            return {"db": path.name, "table": table, "columns": rows}
        except Exception as e:
            logger.error(f"describe failed for '{table}' in '{path.name}': {e}")
            return {"error": f"describe failed: {e}"}

    if op in ("execute", "exec", "query"):
        db = params.get("db")
        sql = params.get("query")
        sql_params = params.get("params")  # list/tuple/dict or list of these when many=True
        many = bool(params.get("many", False))
        return_rows_param = params.get("return_rows")
        limit_param = params.get("limit", 100)  # default 100

        if not isinstance(db, str) or not db.strip():
            logger.warning("execute: missing or invalid 'db' parameter")
            return {"error": "db is required (string)"}
        if not isinstance(sql, str) or not sql.strip():
            logger.warning("execute: missing or invalid 'query' parameter")
            return {"error": "query is required (string)"}

        # Validate query size
        if len(sql) > 51200:
            logger.warning(f"execute: query too large ({len(sql)} bytes, max 50KB)")
            return {"error": "query exceeds 50KB limit"}

        try:
            path = _db_path(db, must_exist=True)
        except FileNotFoundError as e:
            logger.warning(f"execute: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.warning(f"execute: invalid db '{db}': {e}")
            return {"error": str(e)}

        try:
            conn = sqlite3.connect(str(path))
            conn.row_factory = _row_factory
            cur = conn.cursor()
            try:
                if many:
                    # Expect sql_params to be a list of param sets
                    if not isinstance(sql_params, (list, tuple)):
                        logger.warning("execute: 'params' must be a list when many=True")
                        return {"error": "params must be a list when many=True"}
                    cur.executemany(sql, sql_params)  # type: ignore[arg-type]
                    conn.commit()
                    rows = []
                    columns: List[str] = []
                    logger.info(f"execute: executemany completed ({cur.rowcount} rows affected)")
                else:
                    if sql_params is None:
                        cur.execute(sql)
                    else:
                        cur.execute(sql, sql_params)
                    # SELECT-like returns rows; others return rowcount/lastrowid
                    if return_rows_param is None:
                        want_rows = _is_select_like(sql)
                    else:
                        want_rows = bool(return_rows_param)
                    if want_rows and cur.description is not None:
                        all_rows = cur.fetchall()
                        columns = [c[0] for c in cur.description]
                        
                        # Apply limit and truncation warning
                        total_count = len(all_rows)
                        actual_limit = min(limit_param, 1000)  # enforce max 1000
                        if total_count > actual_limit:
                            rows = all_rows[:actual_limit]
                            logger.warning(f"execute: truncated results from {total_count} to {actual_limit} rows")
                        else:
                            rows = all_rows
                    else:
                        rows = []
                        columns = []
                    conn.commit()
                    logger.info(f"execute: query completed ({len(rows)} rows returned)")

                result: Dict[str, Any] = {"db": path.name}
                if rows:
                    result.update({"columns": columns, "rows": rows, "returned_count": len(rows)})
                    if total_count > len(rows):
                        result["truncated"] = True
                        result["total_count"] = total_count
                        result["warning"] = f"Results truncated: {total_count} found, returning {len(rows)} (limit: {actual_limit})"
                else:
                    # For non-SELECT queries, include rowcount/lastrowid
                    result.update({"rowcount": cur.rowcount, "lastrowid": cur.lastrowid})
                return result
            finally:
                cur.close(); conn.close()
        except Exception as e:
            logger.error(f"execute failed: {e}")
            return {"error": f"execute failed: {e}"}

    if op == "executescript":
        db = params.get("db"); script = params.get("script")
        if not isinstance(db, str) or not db.strip():
            logger.warning("executescript: missing or invalid 'db' parameter")
            return {"error": "db is required (string)"}
        if not isinstance(script, str) or not script.strip():
            logger.warning("executescript: missing or invalid 'script' parameter")
            return {"error": "script is required (string)"}
        
        # Validate script size
        if len(script) > 51200:
            logger.warning(f"executescript: script too large ({len(script)} bytes, max 50KB)")
            return {"error": "script exceeds 50KB limit"}
        
        try:
            path = _db_path(db, must_exist=True)
        except FileNotFoundError as e:
            logger.warning(f"executescript: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.warning(f"executescript: invalid db '{db}': {e}")
            return {"error": str(e)}
        try:
            conn = sqlite3.connect(str(path))
            cur = conn.cursor()
            try:
                cur.executescript(script)
                conn.commit()
                logger.info(f"executescript: script executed successfully on {path.name}")
                return {"db": path.name}
            finally:
                cur.close(); conn.close()
        except Exception as e:
            logger.error(f"executescript failed for '{path.name}': {e}")
            return {"error": f"executescript failed: {e}"}

    logger.warning(f"Unknown operation: {operation}")
    return {"error": f"Unknown operation: {operation}"}


def spec() -> Dict[str, Any]:
    # Load the canonical JSON spec (source of truth)
    return _load_spec_json("sqlite_db")
