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
- execute(db, query, params?, many?, return_rows?) -> run SQL and return rows/metrics
- executescript(db, script) -> run multiple statements in one call

Notes:
- The parameter "db" and "name" refer to the logical DB name (with or without .db).
- DB files are created in <PROJECT_ROOT>/sqlite3 and paths are sanitized (alnum, _ and -).
"""
from __future__ import annotations

import os
import re
import sqlite3
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


def _db_path(name: str) -> Path:
    norm = _normalize_name(name)
    return (BASE_DIR / norm).resolve()


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
        return {"success": True, **_ensure_dir()}

    if op == "list_dbs":
        _ensure_dir()
        items = sorted([p.name for p in BASE_DIR.glob("*.db") if p.is_file()])
        return {"success": True, "base_dir": str(BASE_DIR), "databases": items}

    if op == "create_db":
        name = params.get("name")
        schema = params.get("schema")  # optional SQL script
        if not isinstance(name, str) or not name.strip():
            return {"error": "name is required (string)"}
        try:
            path = _db_path(name)
        except Exception as e:
            return {"error": str(e)}
        _ensure_dir()
        try:
            must_init = not path.exists()
            conn = sqlite3.connect(str(path))
            try:
                if schema and isinstance(schema, str):
                    conn.executescript(schema)
                    conn.commit()
            finally:
                conn.close()
            return {"success": True, "db": path.name, "path": str(path), "created": must_init}
        except Exception as e:
            return {"error": f"create_db failed: {e}"}

    if op == "delete_db":
        name = params.get("name")
        if not isinstance(name, str) or not name.strip():
            return {"error": "name is required (string)"}
        try:
            path = _db_path(name)
        except Exception as e:
            return {"error": str(e)}
        if not path.exists():
            return {"error": f"database not found: {path.name}"}
        try:
            path.unlink()
            return {"success": True, "deleted": path.name}
        except Exception as e:
            return {"error": f"delete_db failed: {e}"}

    if op == "get_tables":
        db = params.get("db")
        if not isinstance(db, str) or not db.strip():
            return {"error": "db is required (string)"}
        path = _db_path(db)
        if not path.exists():
            return {"error": f"database not found: {path.name}"}
        try:
            conn = sqlite3.connect(str(path))
            conn.row_factory = _row_factory
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            rows = cur.fetchall()
            cur.close(); conn.close()
            return {"success": True, "db": path.name, "tables": [r.get("name") for r in rows]}
        except Exception as e:
            return {"error": f"get_tables failed: {e}"}

    if op == "describe":
        db = params.get("db"); table = params.get("table")
        if not isinstance(db, str) or not db.strip():
            return {"error": "db is required (string)"}
        if not isinstance(table, str) or not table.strip():
            return {"error": "table is required (string)"}
        path = _db_path(db)
        if not path.exists():
            return {"error": f"database not found: {path.name}"}
        try:
            conn = sqlite3.connect(str(path))
            conn.row_factory = _row_factory
            cur = conn.cursor()
            cur.execute(f"PRAGMA table_info({table})")
            rows = cur.fetchall()
            cur.close(); conn.close()
            return {"success": True, "db": path.name, "table": table, "columns": rows}
        except Exception as e:
            return {"error": f"describe failed: {e}"}

    if op in ("execute", "exec", "query"):
        db = params.get("db")
        sql = params.get("query")
        sql_params = params.get("params")  # list/tuple/dict or list of these when many=True
        many = bool(params.get("many", False))
        return_rows_param = params.get("return_rows")

        if not isinstance(db, str) or not db.strip():
            return {"error": "db is required (string)"}
        if not isinstance(sql, str) or not sql.strip():
            return {"error": "query is required (string)"}

        path = _db_path(db)
        if not path.exists():
            return {"error": f"database not found: {path.name}"}

        try:
            conn = sqlite3.connect(str(path))
            conn.row_factory = _row_factory
            cur = conn.cursor()
            try:
                if many:
                    # Expect sql_params to be a list of param sets
                    if not isinstance(sql_params, (list, tuple)):
                        return {"error": "params must be a list when many=True"}
                    cur.executemany(sql, sql_params)  # type: ignore[arg-type]
                    conn.commit()
                    rows = []
                    columns: List[str] = []
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
                        rows = cur.fetchall()
                        columns = [c[0] for c in cur.description]
                    else:
                        rows = []
                        columns = []
                    conn.commit()
                result: Dict[str, Any] = {
                    "success": True,
                    "db": path.name,
                    "rowcount": cur.rowcount,
                    "lastrowid": cur.lastrowid,
                }
                if rows:
                    result.update({"columns": columns, "rows": rows, "rows_count": len(rows)})
                return result
            finally:
                cur.close(); conn.close()
        except Exception as e:
            return {"error": f"execute failed: {e}"}

    if op == "executescript":
        db = params.get("db"); script = params.get("script")
        if not isinstance(db, str) or not db.strip():
            return {"error": "db is required (string)"}
        if not isinstance(script, str) or not script.strip():
            return {"error": "script is required (string)"}
        path = _db_path(db)
        if not path.exists():
            return {"error": f"database not found: {path.name}"}
        try:
            conn = sqlite3.connect(str(path))
            cur = conn.cursor()
            try:
                cur.executescript(script)
                conn.commit()
                return {"success": True, "db": path.name}
            finally:
                cur.close(); conn.close()
        except Exception as e:
            return {"error": f"executescript failed: {e}"}

    return {"error": f"Unknown operation: {operation}"}


def spec() -> Dict[str, Any]:
    # Load the canonical JSON spec (source of truth)
    return _load_spec_json("sqlite_db")
