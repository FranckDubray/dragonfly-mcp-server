import json, logging
from typing import Any, Dict, List
from .constants import TOOL_SPECS_DIR
from .meta import get_meta_json
logger = logging.getLogger(__name__)

def normalize_tool_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    try:
        f = spec.get("function") if isinstance(spec, dict) else None
    except Exception:
        f = None
    core = f if isinstance(f, dict) else spec
    if not isinstance(core, dict):
        raise ValueError("Invalid tool spec: not a dict")
    name = core.get("name") or "worker_query"
    description = core.get("description") or "Execute une requête SQL SELECT en lecture seule sur la base du worker."
    parameters = core.get("parameters") or {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Requête SELECT (lecture seule)"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 50},
        },
        "required": ["query"],
        "additionalProperties": False,
    }
    return {"type": "function", "name": name, "description": description, "parameters": parameters}

def load_worker_query_tool_spec() -> Dict[str, Any]:
    p = TOOL_SPECS_DIR / "worker_query.json"
    if not p.exists():
        logger.error("worker_query.json introuvable dans tool_specs; fallback minimal appliqué")
        return normalize_tool_spec({})
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return normalize_tool_spec(data)
    except Exception as e:
        logger.error(f"Failed to parse worker_query.json: {e}")
        return normalize_tool_spec({})

def resolve_tools(meta: dict) -> List[Dict[str,Any]]:
    tools_json = get_meta_json(meta, 'tools_json', default=None)
    resolved: List[Dict[str,Any]] = []

    def add_worker_query():
        try:
            resolved.append(load_worker_query_tool_spec())
        except Exception as e:
            logger.error(f"Failed to load worker_query tool spec: {e}")

    if isinstance(tools_json, list) and tools_json:
        for item in tools_json:
            if isinstance(item, str):
                if item == 'worker_query':
                    add_worker_query()
                else:
                    logger.warning(f"Unknown tool name in DB: {item} (ignored)")
            elif isinstance(item, dict):
                if item.get('type') == 'function' and item.get('name') and item.get('parameters'):
                    resolved.append(item)
                else:
                    logger.warning("Invalid tool spec in DB (ignored)")
    else:
        add_worker_query()

    if not resolved:
        add_worker_query()

    return resolved
