"""Core logic for custom model management."""
from __future__ import annotations
import json
import re
import logging
from typing import Dict, Any, Optional

from .mysql import (
    query,
    get_model_full,
    model_name_exists,
    insert_model_from_source,
    update_field,
    get_model_tools,
    add_model_tools,
    remove_model_tools,
)

LOG = logging.getLogger(__name__)


def _hardcode_model_in_input(input_json: str, source_name: str) -> str:
    """Replace '{{model}}' with the actual source model name in input."""
    return input_json.replace('"{{model}}"', f'"{source_name}"')


def _patch_config_for_custom(config_json: str) -> str:
    """Force toolsAvailable=false and executeToolsDirectly=true."""
    try:
        cfg = json.loads(config_json)
    except (json.JSONDecodeError, TypeError):
        return config_json
    cfg["toolsAvailable"] = False
    cfg["executeToolsDirectly"] = True
    return json.dumps(cfg)


# ── list ──────────────────────────────────────────────────

def list_customs(limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    """List custom models (those with executeToolsDirectly in config)."""
    count_r = query(
        "SELECT COUNT(*) as total FROM models "
        "WHERE config LIKE '%executeToolsDirectly%'"
    )
    total = 0
    if "error" not in count_r and count_r.get("rows"):
        total = count_r["rows"][0].get("total", 0)

    data_r = query(
        "SELECT m.id, m.name, m.display_name, m.active, m.position, "
        "m.category, e.name as editor, "
        "LEFT(m.preprompt, 80) as preprompt_preview "
        "FROM models m JOIN editor e ON m.editor_id = e.id "
        "WHERE m.config LIKE '%executeToolsDirectly%' "
        f"ORDER BY m.id LIMIT {limit} OFFSET {offset}"
    )
    if "error" in data_r:
        return data_r

    return {
        "customs": data_r.get("rows", []),
        "returned_count": data_r.get("returned_count", 0),
        "total_count": total,
        "has_more": (offset + data_r.get("returned_count", 0)) < total,
    }


# ── preview / create ─────────────────────────────────────

def preview_create(
    source_model_id: int, name: str, display_name: str
) -> Dict[str, Any]:
    """Preview what would be created — no modifications."""
    source = get_model_full(source_model_id)
    if not source:
        return {"error": f"Source model {source_model_id} not found"}

    if model_name_exists(name):
        return {"error": f"Model name '{name}' already exists"}

    # Preview only — show what the input/config would look like
    new_input = _hardcode_model_in_input(
        source.get("input", ""), source["name"]
    )
    new_config = _patch_config_for_custom(source.get("config", "{}"))

    return {
        "dry_run": True,
        "source_model": {
            "id": source["id"],
            "name": source["name"],
            "display_name": source.get("display_name"),
            "editor_id": source.get("editor_id"),
        },
        "custom_will_be": {
            "name": name,
            "display_name": display_name,
            "editor_id": source.get("editor_id"),
            "category": source.get("category"),
            "variable": source.get("variable"),
            "active": 0,
            "position": 99,
            "input_preview": new_input[:200],
            "config_preview": new_config[:200],
        },
    }


def create_custom(
    source_model_id: int, name: str, display_name: str
) -> Dict[str, Any]:
    """Create a custom model based on a source model.

    Uses INSERT INTO ... SELECT with REPLACE entirely server-side
    to avoid escaping issues through SSH.
    """
    source = get_model_full(source_model_id)
    if not source:
        return {"error": f"Source model {source_model_id} not found"}

    if model_name_exists(name):
        return {"error": f"Model name '{name}' already exists"}

    result = insert_model_from_source(
        source_model_id=source_model_id,
        name=name,
        display_name=display_name,
        position=99,
    )
    if "error" in result:
        return result

    new_id = result["new_id"]
    LOG.info(
        "✅ Custom '%s' (id=%d) created from '%s' (id=%d)",
        name, new_id, source["name"], source_model_id,
    )

    return {
        "created": True,
        "model_id": new_id,
        "name": name,
        "display_name": display_name,
        "source_model": source["name"],
        "source_model_id": source_model_id,
        "active": 0,
    }


# ── activate ──────────────────────────────────────────────

def set_active(model_id: int, active: bool) -> Dict[str, Any]:
    """Activate or deactivate a custom model. NEVER deletes."""
    model = get_model_full(model_id)
    if not model:
        return {"error": f"Model {model_id} not found"}

    val = 1 if active else 0
    if model.get("active") == val:
        state = "active" if active else "inactive"
        return {"error": f"Model already {state}", "model_id": model_id}

    result = update_field(model_id, "active", val)
    if "error" in result:
        return result

    state = "activated" if active else "deactivated"
    LOG.info("🔧 Model '%s' (id=%d) %s", model["name"], model_id, state)
    return {
        "model_id": model_id,
        "name": model["name"],
        "active": active,
    }


# ── set_position ──────────────────────────────────────────

def set_position(model_id: int, position: int) -> Dict[str, Any]:
    """Change display position."""
    model = get_model_full(model_id)
    if not model:
        return {"error": f"Model {model_id} not found"}

    old_pos = model.get("position")
    result = update_field(model_id, "position", position)
    if "error" in result:
        return result

    LOG.info(
        "📍 Model '%s' position: %s → %d", model["name"], old_pos, position
    )
    return {
        "model_id": model_id,
        "name": model["name"],
        "old_position": old_pos,
        "new_position": position,
    }


# ── set_preprompt ─────────────────────────────────────────

def set_preprompt(model_id: int, preprompt: str) -> Dict[str, Any]:
    """Set or clear the system prompt (preprompt)."""
    model = get_model_full(model_id)
    if not model:
        return {"error": f"Model {model_id} not found"}

    val = preprompt if preprompt else None
    result = update_field(model_id, "preprompt", val)
    if "error" in result:
        return result

    action = "cleared" if not preprompt else "updated"
    LOG.info("📝 Model '%s' preprompt %s", model["name"], action)
    return {
        "model_id": model_id,
        "name": model["name"],
        "preprompt_action": action,
        "preprompt_length": len(preprompt) if preprompt else 0,
    }


# ── tools management ─────────────────────────────────────

def list_model_tools(
    model_id: int, limit: int = 20, offset: int = 0
) -> Dict[str, Any]:
    """List tools associated with a custom model."""
    model = get_model_full(model_id)
    if not model:
        return {"error": f"Model {model_id} not found"}

    result = get_model_tools(model_id, limit, offset)
    result["model_id"] = model_id
    result["model_name"] = model["name"]
    return result


def add_tools(model_id: int, tool_ids: list) -> Dict[str, Any]:
    """Add tools to a custom model."""
    model = get_model_full(model_id)
    if not model:
        return {"error": f"Model {model_id} not found"}

    result = add_model_tools(model_id, tool_ids)
    if "error" in result:
        return result

    LOG.info(
        "🔧 Added %d tools to '%s' (id=%d)",
        len(tool_ids), model["name"], model_id,
    )
    return {
        "model_id": model_id,
        "name": model["name"],
        "tools_added": tool_ids,
        "count": len(tool_ids),
    }


def remove_tools(model_id: int, tool_ids: list) -> Dict[str, Any]:
    """Remove tools from a custom model."""
    model = get_model_full(model_id)
    if not model:
        return {"error": f"Model {model_id} not found"}

    result = remove_model_tools(model_id, tool_ids)
    if "error" in result:
        return result

    LOG.info(
        "🗑️ Removed %d tools from '%s' (id=%d)",
        len(tool_ids), model["name"], model_id,
    )
    return {
        "model_id": model_id,
        "name": model["name"],
        "tools_removed": tool_ids,
        "count": len(tool_ids),
    }


# ── update ────────────────────────────────────────────────

def update_model(
    model_id: int,
    display_name: Optional[str] = None,
    config: Optional[str] = None,
    input_json: Optional[str] = None,
) -> Dict[str, Any]:
    """Update custom model fields."""
    model = get_model_full(model_id)
    if not model:
        return {"error": f"Model {model_id} not found"}

    updated = []
    if display_name is not None:
        r = update_field(model_id, "display_name", display_name)
        if "error" in r:
            return r
        updated.append("display_name")

    if config is not None:
        r = update_field(model_id, "config", config)
        if "error" in r:
            return r
        updated.append("config")

    if input_json is not None:
        r = update_field(model_id, "input", input_json)
        if "error" in r:
            return r
        updated.append("input")

    if not updated:
        return {"error": "No fields to update"}

    LOG.info("✏️ Model '%s' updated: %s", model["name"], ", ".join(updated))
    return {
        "model_id": model_id,
        "name": model["name"],
        "updated_fields": updated,
    }
