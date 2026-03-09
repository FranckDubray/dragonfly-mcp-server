
"""MySQL operations for custom model management."""
from __future__ import annotations
import json
import logging
from typing import Dict, Any, List, Optional

from tools._portal_db.utils import run_mysql_via_ssh, parse_tsv, parse_xml

LOG = logging.getLogger(__name__)


def query(sql: str, timeout: int = 30) -> Dict[str, Any]:
    """Execute read query (TSV mode)."""
    result = run_mysql_via_ssh(sql, timeout=timeout)
    if not result["success"]:
        return {"error": result["error"]}
    return parse_tsv(result["stdout"])


def query_xml(sql: str, timeout: int = 30) -> Dict[str, Any]:
    """Execute read query (XML mode — handles multiline fields)."""
    result = run_mysql_via_ssh(sql, timeout=timeout, output_format="xml")
    if not result["success"]:
        return {"error": result["error"]}
    return parse_xml(result["stdout"])


def write(sql: str, timeout: int = 30) -> Dict[str, Any]:
    """Execute write query."""
    result = run_mysql_via_ssh(sql, timeout=timeout)
    if not result["success"]:
        return {"error": result["error"]}
    return {"success": True, "stdout": result["stdout"]}


def get_model_full(model_id: int) -> Optional[Dict[str, Any]]:
    """Get full model info including input/config/variable.

    Uses XML format to handle multiline JSON fields correctly.
    """
    r = query_xml(
        f"SELECT id, name, display_name, editor_id, active, "
        f"input, config, preprompt, variable, category, position "
        f"FROM models WHERE id = {model_id}"
    )
    if "error" in r or not r.get("rows"):
        return None
    return r["rows"][0]


def model_name_exists(name: str) -> bool:
    """Check if a model name already exists."""
    safe = name.replace("'", "\\'")
    r = query(f"SELECT COUNT(*) as c FROM models WHERE name = '{safe}'")
    if "error" in r or not r.get("rows"):
        return False
    return r["rows"][0].get("c", 0) > 0


def _esc(val) -> str:
    """Escape a value for SQL.

    Only escapes single quotes. Backslashes are left as-is because
    values from MySQL TSV output already contain literal backslash
    sequences (e.g. \\n) that must be preserved when re-inserted.
    """
    if val is None:
        return "NULL"
    return "'" + str(val).replace("'", "\\'") + "'"


def insert_model_from_source(
    source_model_id: int,
    name: str,
    display_name: str,
    position: int = 99,
) -> Dict[str, Any]:
    """INSERT a custom model by copying from source, all server-side.

    Does INSERT INTO ... SELECT with REPLACE to hardcode the model name
    and patch the config. No value transits through Python — avoids
    all escaping issues.
    """
    safe_name = _esc(name)
    safe_display = _esc(display_name)

    sql = (
        "INSERT INTO models "
        "(name, display_name, editor_id, input, config, "
        "variable, category, preprompt, position, active) "
        "SELECT "
        f"{safe_name}, "
        f"{safe_display}, "
        "editor_id, "
        # input: hardcode the model name
        "REPLACE(input, '\"{{model}}\"', "
        f"CONCAT('\"', name, '\"')), "
        # config: force toolsAvailable=false, add executeToolsDirectly=true
        "REPLACE("
        "REPLACE(config, "
        "'\"toolsAvailable\": true', "
        "'\"toolsAvailable\": false'), "
        "'\"toolsAvailable\":true', "
        "'\"toolsAvailable\":false'), "
        "variable, "
        "category, "
        "NULL, "
        f"{position}, "
        "0 "
        f"FROM models WHERE id = {source_model_id}"
    )
    result = write(sql, timeout=30)
    if "error" in result:
        return result

    # Now add executeToolsDirectly if not present
    # First get the new model id
    id_r = query(f"SELECT id FROM models WHERE name = {safe_name}")
    if "error" in id_r or not id_r.get("rows"):
        return {"error": "Insert succeeded but could not retrieve new ID"}
    new_id = id_r["rows"][0]["id"]

    # Add executeToolsDirectly to config if not already there
    write(
        f"UPDATE models SET config = "
        f"IF(config LIKE '%executeToolsDirectly%', config, "
        f"REPLACE(config, '}}', ', \"executeToolsDirectly\":true}}')) "
        f"WHERE id = {new_id}"
    )

    return {"success": True, "new_id": new_id}


def insert_model(
    name: str,
    display_name: str,
    editor_id: int,
    input_json: str,
    config_json: str,
    variable: Optional[str],
    category: Optional[str],
    preprompt: Optional[str],
    position: int = 99,
) -> Dict[str, Any]:
    """INSERT a new model row. Returns the new ID."""
    sql = (
        "INSERT INTO models "
        "(name, display_name, editor_id, input, config, "
        "variable, category, preprompt, position, active) "
        f"VALUES ({_esc(name)}, {_esc(display_name)}, {editor_id}, "
        f"{_esc(input_json)}, {_esc(config_json)}, "
        f"{_esc(variable)}, {_esc(category)}, {_esc(preprompt)}, "
        f"{position}, 0)"
    )
    result = write(sql, timeout=30)
    if "error" in result:
        return result

    # Retrieve ID by name (LAST_INSERT_ID unreliable across SSH sessions)
    id_r = query(f"SELECT id FROM models WHERE name = {_esc(name)}")
    if "error" in id_r or not id_r.get("rows"):
        return {"error": "Insert succeeded but could not retrieve new ID"}
    return {"success": True, "new_id": id_r["rows"][0]["id"]}


def update_field(model_id: int, field: str, value: Any) -> Dict[str, Any]:
    """Update a single field on a model."""
    if value is None:
        val_sql = "NULL"
    elif isinstance(value, (int, float, bool)):
        val_sql = str(int(value) if isinstance(value, bool) else value)
    else:
        val_sql = _esc(value)
    sql = f"UPDATE models SET {field} = {val_sql} WHERE id = {model_id}"
    return write(sql)


def get_model_tools(
    model_id: int, limit: int = 20, offset: int = 0
) -> Dict[str, Any]:
    """Get tools associated with a model."""
    count_r = query(
        f"SELECT COUNT(*) as total FROM models_tools "
        f"WHERE models_id = {model_id}"
    )
    total = 0
    if "error" not in count_r and count_r.get("rows"):
        total = count_r["rows"][0].get("total", 0)

    data_r = query(
        f"SELECT mt.tools_id, t.title, t.display_name, t.is_active "
        f"FROM models_tools mt "
        f"JOIN tools t ON mt.tools_id = t.id "
        f"WHERE mt.models_id = {model_id} "
        f"ORDER BY mt.tools_id "
        f"LIMIT {limit} OFFSET {offset}"
    )
    if "error" in data_r:
        return data_r

    return {
        "rows": data_r.get("rows", []),
        "returned_count": data_r.get("returned_count", 0),
        "total_count": total,
        "has_more": (offset + data_r.get("returned_count", 0)) < total,
    }


def add_model_tools(model_id: int, tool_ids: List[int]) -> Dict[str, Any]:
    """Add tools to a model (INSERT IGNORE for idempotency)."""
    if not tool_ids:
        return {"error": "No tool_ids provided"}
    values = ", ".join(f"({model_id}, {tid})" for tid in tool_ids)
    sql = (
        f"INSERT IGNORE INTO models_tools (models_id, tools_id) "
        f"VALUES {values}"
    )
    result = write(sql)
    if "error" in result:
        return result
    return {"success": True, "added": len(tool_ids)}


def remove_model_tools(model_id: int, tool_ids: List[int]) -> Dict[str, Any]:
    """Remove tools from a model."""
    if not tool_ids:
        return {"error": "No tool_ids provided"}
    ids_str = ",".join(str(t) for t in tool_ids)
    sql = (
        f"DELETE FROM models_tools "
        f"WHERE models_id = {model_id} AND tools_id IN ({ids_str})"
    )
    return write(sql)

 
