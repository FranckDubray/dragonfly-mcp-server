
import json, os

def spec():
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'py_orchestrator.json'))
    if os.path.exists(spec_path):
        with open(spec_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    # Minimal dynamic spec (fallback dev) if canonical spec not present yet
    return {
        "type": "function",
        "function": {
            "name": "py_orchestrator",
            "displayName": "Python Orchestrator",
            "category": "intelligence",
            "description": "Run Python step-by-step workflows (no JSON graph). Start/stop/status/debug, same contracts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": ["start","stop","status","debug","list"]},
                    "worker_name": {"type": "string"},
                    "worker_file": {"type": "string", "description": "Path under workers_py/ <module>.py"},
                    "hot_reload": {"type": "boolean", "default": True},
                    "debug": {"type": "object"}
                },
                "required": ["operation"],
                "additionalProperties": False
            }
        }
    }


def run(**params):
    from ._py_orchestrator.api import start_or_control
    return start_or_control(params)
