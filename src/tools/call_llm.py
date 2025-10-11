from typing import Any, Dict
from ._call_llm.core import execute_call_llm


def run(operation: str = "run", **params) -> Dict[str, Any]:
    """Facade for call_llm tool. Requires 'model' explicitly.
    Expected params: message (str), model (str), optional promptSystem, max_tokens, tool_names (list[str]), debug (bool)
    """
    # Enforce required param at code level (in addition to JSON spec)
    if not params.get("model"):
        return {"error": "Missing required parameter: model"}

    # Allow simple call with message only (legacy) — but model must be present
    messages = params.pop("messages", None)
    if not messages:
        msg = params.pop("message", None)
        if not msg:
            return {"error": "Missing required parameter: message"}
        messages = [{"role": "user", "content": msg}]

    model = params.pop("model")
    max_tokens = params.pop("max_tokens", None)
    tool_names = params.pop("tool_names", None)
    # promptSystem passed separately, not in messages
    promptSystem = params.pop("promptSystem", None)
    debug = params.pop("debug", False)

    # Any extra params are ignored (spec has additionalProperties: false), but tolerate silently
    result = execute_call_llm(messages=messages, model=model, max_tokens=max_tokens, tool_names=tool_names, promptSystem=promptSystem, debug=debug)
    return result


def spec() -> Dict[str, Any]:
    # Load canonical JSON spec (source of truth)
    import json, os
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'call_llm.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)
