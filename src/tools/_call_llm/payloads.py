from typing import Any, Dict, List, Optional, Tuple
import copy


def strip_system_to_promptSystem(messages: List[Dict[str, Any]], explicit: Optional[str]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    if explicit:
        return messages, explicit
    prompt = None
    new_msgs: List[Dict[str, Any]] = []
    for m in messages:
        if m.get("role") == "system" and prompt is None:
            prompt = m.get("content", "")
        else:
            new_msgs.append(m)
    return new_msgs, prompt


def build_initial_payload(
    model: str,
    messages: List[Dict[str, Any]],
    prompt_system: Optional[str],
    max_tokens: Optional[int],
    assistant_id: Optional[str] = None,
    temperature: Optional[float] = None,
) -> Dict[str, Any]:
    p: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 1 if (temperature is None) else temperature,
    }
    if prompt_system:
        p["promptSystem"] = prompt_system
    if max_tokens:
        p["max_tokens"] = max_tokens
    if assistant_id:
        p["assistantId"] = assistant_id
    return p


def summarize_payload(payload: Dict[str, Any], tool_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    out = {
        "model": payload.get("model"),
        "has_promptSystem": "promptSystem" in payload and bool(payload.get("promptSystem")),
        "messages_count": len(payload.get("messages") or []),
        "stream": bool(payload.get("stream")),
    }
    if tool_data:
        out.update({
            "tools_count": len(tool_data.get("tools") or []),
            "tool_names": list(tool_data.get("found_tools") or []),
        })
    return out
