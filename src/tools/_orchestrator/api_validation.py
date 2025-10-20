# API validation helpers - Process validation logic (<4KB)

from pathlib import Path
from typing import Any, Dict, Optional

# Optional JSON schema
try:
    from jsonschema import validate as validate_schema, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    ValidationError = None

SCHEMA_PATH = Path(__file__).parent / 'schemas' / 'process.schema.json'
PROCESS_SCHEMA = None
if SCHEMA_PATH.exists():
    try:
        import json
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            PROCESS_SCHEMA = json.load(f)
    except Exception:
        PROCESS_SCHEMA = None


def validate_process_schema(process_data: dict) -> Optional[Dict[str, Any]]:
    """
    Validate process against JSON schema.
    
    Returns:
        Error dict if validation fails, None if OK
    """
    if not JSONSCHEMA_AVAILABLE or not PROCESS_SCHEMA:
        return None
    try:
        validate_schema(instance=process_data, schema=PROCESS_SCHEMA)
    except ValidationError as e:
        return {
            "accepted": False,
            "status": "failed",
            "message": f"Invalid process schema: {e.message[:250]}",
            "validation_path": list(e.absolute_path) if e.absolute_path else [],
            "schema_path": list(e.absolute_schema_path) if e.absolute_schema_path else [],
            "truncated": False
        }
    return None


def validate_process_logic(process_data: dict) -> Optional[str]:
    """
    Custom validation rules (beyond JSON schema).
    
    Returns:
        Error message string if validation fails, None if OK
    """
    # Guard: no top-level $import (must import under graph)
    if "$import" in process_data:
        return "Top-level $import not allowed (use graph.$import to preserve worker_ctx)"

    if not isinstance(process_data.get('worker_ctx'), dict):
        return "worker_ctx must be an object (and must include db_name)"
    if not process_data['worker_ctx'].get('db_name'):
        return "worker_ctx.db_name required (single data DB per worker)"

    graph = process_data.get('graph', {})
    if not isinstance(graph, dict) or not graph:
        return "graph must be an object (import under graph if splitting)"

    nodes = graph.get('nodes', [])
    edges = graph.get('edges', [])
    if not nodes:
        return "Graph must have at least one node"

    node_names = {n['name'] for n in nodes}
    if len(node_names) != len(nodes):
        names_list = [n['name'] for n in nodes]
        duplicates = [name for name in names_list if names_list.count(name) > 1]
        return f"Duplicate node names: {', '.join(set(duplicates))}"

    start_nodes = [n for n in nodes if n.get('type') == 'start']
    if len(start_nodes) == 0:
        return "No START node found (type='start' required)"
    if len(start_nodes) > 1:
        return f"Multiple START nodes found: {', '.join(n['name'] for n in start_nodes)}"

    for i, edge in enumerate(edges):
        from_node = edge.get('from')
        to_node = edge.get('to')
        if from_node not in node_names:
            return f"Edge #{i}: 'from' references unknown node '{from_node}'"
        if to_node not in node_names:
            return f"Edge #{i}: 'to' references unknown node '{to_node}'"

    edge_signatures = [(e.get('from'), e.get('when', 'always')) for e in edges]
    if len(edge_signatures) != len(set(edge_signatures)):
        duplicates = [sig for sig in edge_signatures if edge_signatures.count(sig) > 1]
        return f"Duplicate edges detected: {duplicates[:3]}"

    # Optional: basic call_llm sanity (presence of messages)
    for n in nodes:
        if n.get('type') == 'io' and n.get('handler') == 'http_tool':
            inp = n.get('inputs', {}) or {}
            if inp.get('tool') == 'call_llm':
                # messages must exist after resolution; we only check presence here
                if 'messages' not in inp:
                    return f"LLM node '{n.get('name')}' missing 'messages'"

    return None
