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
- execute(db, query, params?, many?, return_rows?, limit?, read_only?) -> run SQL and return rows/metrics
- exec/ query are aliases of execute for convenience
- executescript(db, script, read_only?) -> run multiple statements in one call

Notes:
- The parameter "db" and "name" refer to the logical DB name (with or without .db).
- DB files are created in <PROJECT_ROOT>/sqlite3 and paths are sanitized (alnum, _ and -).
- LIMIT parameter (default: 100, max: 1000): For SELECT queries, automatically truncates results
  to avoid massive outputs. Add explicit LIMIT clause in your query for precise control.
- Case-insensitive matching: "alain" will match both "worker_alain.db" and "worker_Alain.db"
- read_only (bool, default False): when True, only SELECT/PRAGMA/WITH queries are allowed and the
  connection is opened in SQLite RO mode (URI). executemany/executescript are disabled in read-only.
"""
from __future__ import annotations

import re
import sqlite3
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json

try:
    from config import find_project_root
except Exception:
    from pathlib import Path as _P
    find_project_root = lambda: _P.cwd()  # type: ignore

PROJECT_ROOT = find_project_root()
BASE_DIR = PROJECT_ROOT / "sqlite3"
BASE_DIR.mkdir(parents=True, exist_ok=True)
_SPEC_DIR = Path(__file__).resolve().parent.parent / "tool_specs"

_DB_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+(\.db)?$")

logger = logging.getLogger(__name__)


def _load_spec_json(name: str) -> Dict[str, Any]:
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
    """Resolve database path with case-insensitive matching."""
    norm = _normalize_name(name)
    exact_path = (BASE_DIR / norm).resolve()
    if exact_path.exists():
        return exact_path
    if norm.startswith("worker_"):
        worker_part = norm[7:-3]
        for variant in [
            f"worker_{worker_part}.db",
            f"worker_{worker_part.lower()}.db",
            f"worker_{worker_part.capitalize()}.db",
            f"worker_{worker_part.upper()}.db",
        ]:
            test_path = (BASE_DIR / variant).resolve()
            if test_path.exists():
                logger.info("📁 Matched '%s' → '%s' (case-insensitive)", name, variant)
                return test_path
    if must_exist:
        raise FileNotFoundError(f"Database '{name}' not found in {BASE_DIR}")
    return exact_path


def _row_factory(cursor: sqlite3.Cursor, row: Tuple[Any, ...]) -> Dict[str, Any]:
    return {col[0]: row[i] for i, col in enumerate(cursor.description or [])}


def _is_select_like(sql: str) -> bool:
    s = sql.lstrip().lower()
    return s.startswith("select") or s.startswith("pragma") or s.startswith("with")


def _ensure_dir() -> Dict[str, Any]:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    return {"base_dir": str(BASE_DIR)}


def _want_read_only(params: Dict[str, Any]) -> bool:
    try:
        v = params.get("read_only")
        return bool(v) and str(v).lower() not in {"false","0","no","off"}
    except Exception:
        return False


def _connect(path: Path, read_only: bool = False) -> sqlite3.Connection:
    if read_only:
        # Open with SQLite URI mode=ro
        uri = f"file:{path.as_posix()}?mode=ro"
        return sqlite3.connect(uri, uri=True)
    return sqlite3.connect(str(path))


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
        schema = params.get("schema")
        if not isinstance(name, str) or not name.strip():
            logger.warning("create_db: missing or invalid 'name' parameter")
            return {"error": "name is required (string)"}
        try:
            path = _db_path(name, must_exist=False)
        except Exception as e:
            logger.warning("create_db: invalid name '%s': %s", name, e)
            return {"error": str(e)}
        _ensure_dir()
        try:
            must_init = not path.exists()
            conn = _connect(path, read_only=False)
            try:
                if schema and isinstance(schema, str):
                    if len(schema) > 51200:
                        logger.warning("create_db: schema too large (%d bytes, max 50KB)", len(schema))
                        return {"error": "schema exceeds 50KB limit"}
                    conn.executescript(schema)
                    conn.commit()
            finally:
                conn.close()
            logger.info("create_db: %s %s", 'created' if must_init else 'opened', path.name)
            return {"db": path.name, "path": str(path), "created": must_init}
        except Exception as e:
            logger.error("create_db failed for '%s': %s", name, e)
            return {"error": f"create_db failed: {e}"}

    if op == "delete_db":
        name = params.get("name")
        if not isinstance(name, str) or not name.strip():
            logger.warning("delete_db: missing or invalid 'name' parameter")
            return {"error": "name is required (string)"}
        try:
            path = _db_path(name, must_exist=True)
        except FileNotFoundError as e:
            logger.warning("delete_db: %s", e)
            return {"error": str(e)}
        except Exception as e:
            logger.warning("delete_db: invalid name '%s': %s", name, e)
            return {"error": str(e)}
        try:
            path.unlink()
            logger.info("delete_db: deleted %s", path.name)
            return {"deleted": path.name}
        except Exception as e:
            logger.error("delete_db failed for '%s': %s", path.name, e)
            return {"error": f"delete_db failed: {e}"}

    if op == "get_tables":
        db = params.get("db")
        if not isinstance(db, str) or not db.strip():
            logger.warning("get_tables: missing or invalid 'db' parameter")
            return {"error": "db is required (string)"}
        try:
            path = _db_path(db, must_exist=True)
        except FileNotFoundError as e:
            logger.warning("get_tables: %s", e)
            return {"error": str(e)}
        except Exception as e:
            logger.warning("get_tables: invalid db '%s': %s", db, e)
            return {"error": str(e)}
        try:
            conn = _connect(path, read_only=True)  # harmless read-only for introspection
            conn.row_factory = _row_factory
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            rows = cur.fetchall()
            cur.close(); conn.close()
            tables = [r.get("name") for r in rows]
            logger.info("get_tables: %d tables in %s", len(tables), path.name)
            return {"db": path.name, "tables": tables, "count": len(tables)}
        except Exception as e:
            logger.error("get_tables failed for '%s': %s", path.name, e)
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
            logger.warning("describe: %s", e)
            return {"error": str(e)}
        except Exception as e:
            logger.warning("describe: invalid db '%s': %s", db, e)
            return {"error": str(e)}
        try:
            conn = _connect(path, read_only=True)
            conn.row_factory = _row_factory
            cur = conn.cursor()
            cur.execute(f"PRAGMA table_info({table})")
            rows = cur.fetchall()
            cur.close(); conn.close()
            logger.info("describe: %d columns in %s (%s)", len(rows), table, path.name)
            return {"db": path.name, "table": table, "columns": rows}
        except Exception as e:
            logger.error("describe failed for '%s' in '%s': %s", table, path.name, e)
            return {"error": f"describe failed: {e}"}

    if op in ("execute", "exec", "query"):
        db = params.get("db"); sql = params.get("query"); many = bool(params.get("many", False))
        sql_params = params.get("params")
        return_rows_param = params.get("return_rows")
        limit_param = params.get("limit", 100)
        ro = _want_read_only(params)
        if not isinstance(db, str) or not db.strip():
            logger.warning("execute: missing or invalid 'db' parameter")
            return {"error": "db is required (string)"}
        if not isinstance(sql, str) or not sql.strip():
            logger.warning("execute: missing or invalid 'query' parameter")
            return {"error": "query is required (string)"}
        if len(sql) > 51200:
            logger.warning("execute: query too large (%d bytes, max 50KB)", len(sql))
            return {"error": "query exceeds 50KB limit"}
        # Read-only enforcement per call
        if ro:
            if many:
                return {"error": "read-only mode: executemany disabled"}
            if not _is_select_like(sql):
                return {"error": "read-only mode: only SELECT/PRAGMA/WITH allowed"}
        try:
            path = _db_path(db, must_exist=True)
        except FileNotFoundError as e:
            logger.warning("execute: %s", e)
            return {"error": str(e)}
        except Exception as e:
            logger.warning("execute: invalid db '%s': %s", db, e)
            return {"error": str(e)}
        try:
            conn = _connect(path, read_only=ro)
            conn.row_factory = _row_factory
            cur = conn.cursor()
            try:
                if many:
                    cur.executemany(sql, sql_params if isinstance(sql_params, (list, tuple)) else [])  # type: ignore[arg-type]
                    conn.commit()
                    rows = []; columns: List[str] = []
                    logger.info("execute: executemany completed (%d rows affected)", cur.rowcount)
                else:
                    if sql_params is None:
                        cur.execute(sql)
                    else:
                        cur.execute(sql, sql_params)
                    if (return_rows_param is None and _is_select_like(sql)) or bool(return_rows_param):
                        all_rows = cur.fetchall()
                        columns = [c[0] for c in cur.description or []]
                        total_count = len(all_rows)
                        actual_limit = min(limit_param, 1000)
                        rows = all_rows[:actual_limit]
                        if total_count > actual_limit:
                            logger.warning("execute: truncated results from %d to %d rows", total_count, actual_limit)
                            truncated = True
                        else:
                            truncated = False
                    else:
                        rows = []; columns = []; truncated = False
                    conn.commit()
                    logger.info("execute: query completed (%d rows returned)", len(rows))
                result: Dict[str, Any] = {"db": path.name}
                if rows:
                    result.update({"columns": columns, "rows": rows, "returned_count": len(rows)})
                    if 'total_count' in locals() and total_count > len(rows):
                        result.update({"truncated": True, "total_count": total_count, "warning": f"Results truncated: {total_count} found, returning {len(rows)} (limit: {actual_limit})"})
                else:
                    result.update({"rowcount": getattr(cur, 'rowcount', 0), "lastrowid": getattr(cur, 'lastrowid', None)})
                return result
            finally:
                cur.close(); conn.close()
        except Exception as e:
            logger.error("execute failed: %s", e)
            return {"error": f"execute failed: {e}"}

    if op == "executescript":
        db = params.get("db"); script = params.get("script"); ro = _want_read_only(params)
        if ro:
            return {"error": "read-only mode: executescript disabled"}
        if not isinstance(db, str) or not db.strip():
            logger.warning("executescript: missing or invalid 'db' parameter")
            return {"error": "db is required (string)"}
        if not isinstance(script, str) or not script.strip():
            logger.warning("executescript: missing or invalid 'script' parameter")
            return {"error": "script is required (string)"}
        if len(script) > 51200:
            logger.warning("executescript: script too large (%d bytes, max 50KB)", len(script))
            return {"error": "script exceeds 50KB limit"}
        try:
            path = _db_path(db, must_exist=True)
        except FileNotFoundError as e:
            logger.warning("executescript: %s", e)
            return {"error": str(e)}
        except Exception as e:
            logger.warning("executescript: invalid db '%s': %s", db, e)
            return {"error": str(e)}
        try:
            conn = _connect(path, read_only=False)
            cur = conn.cursor()
            try:
                cur.executescript(script)
                conn.commit()
                logger.info("executescript: script executed successfully on %s", path.name)
                return {"db": path.name}
            finally:
                cur.close(); conn.close()
        except Exception as e:
            logger.error("executescript failed for '%s': %s", path.name, e)
            return {"error": f"executescript failed: {e}"}

    logger.warning("Unknown operation: %s", operation)
    return {"error": f"Unknown operation: {operation}"}


def spec() -> Dict[str, Any]:
    return _load_spec_json("sqlite_db")
