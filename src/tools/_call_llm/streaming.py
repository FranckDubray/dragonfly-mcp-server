"""
Streaming utilities for LLM responses (SSE)
- Supports both text aggregation and tool_calls reconstruction in streaming mode.
"""
import json
import logging

LOG = logging.getLogger(__name__)

def process_streaming_chunks(response):
    """
    Process streaming response and return aggregated text content.
    Expects Server-Sent Events with lines starting by 'data: '.
    Returns: {"content": str, "finish_reason": str, "usage": dict|None}
    """
    content = ""
    finish_reason = None
    usage = None
    for line in response.iter_lines():
        if not line:
            continue
        line = line.decode('utf-8').strip()
        if not line.startswith('data: '):
            continue
        data_str = line[6:]
        if data_str == '[DONE]':
            break
        try:
            chunk = json.loads(data_str)
            # Some gateways wrap under {"response": ...}
            if "response" in chunk and "choices" not in chunk:
                chunk = chunk["response"]
            choices = chunk.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {})
                if delta.get("content"):
                    content += delta["content"]
                if choices[0].get("finish_reason"):
                    finish_reason = choices[0]["finish_reason"]
            if chunk.get("usage"):
                usage = chunk["usage"]
        except Exception:
            continue
    return {"content": content, "finish_reason": finish_reason or "stop", "usage": usage}


def process_tool_calls_stream(response):
    """
    Consume SSE stream and reconstruct tool_calls (OpenAI streaming format) and any text fragments.
    Returns: {
      "tool_calls": [ {"id": str|None, "function": {"name": str|None, "arguments": str}}, ...],
      "text": str,  # any assistant text streamed (if present)
      "finish_reason": str,
      "usage": dict|None
    }
    """
    # index -> entry {"id":..., "function": {"name":..., "arguments": str}}
    calls = {}
    text_buf = []
    finish_reason = None
    usage = None

    for raw in response.iter_lines():
        if not raw:
            continue
        line = raw.decode('utf-8').strip()
        if not line.startswith('data: '):
            continue
        data_str = line[6:]
        if data_str == '[DONE]':
            break
        try:
            obj = json.loads(data_str)
        except Exception:
            continue
        # Unwrap gateway
        if "response" in obj and "choices" not in obj:
            obj = obj["response"]
        choices = obj.get("choices", [])
        if not choices:
            continue
        delta = choices[0].get("delta", {})
        # Aggregate text if any
        if delta.get("content"):
            text_buf.append(delta["content"])
        # Aggregate tool_calls fragments
        for item in delta.get("tool_calls", []) or []:
            idx = item.get("index", 0)
            entry = calls.setdefault(idx, {"id": None, "function": {"name": None, "arguments": ""}})
            if item.get("id"):
                entry["id"] = item["id"]
            fn = item.get("function") or {}
            if fn.get("name"):
                entry["function"]["name"] = fn["name"]
            if fn.get("arguments"):
                entry["function"]["arguments"] += fn["arguments"]
        # Finish reason
        if choices[0].get("finish_reason"):
            finish_reason = choices[0]["finish_reason"]
        # Usage if present
        if obj.get("usage"):
            usage = obj["usage"]

    # Order calls by index
    tool_calls = []
    for idx in sorted(calls.keys()):
        tool_calls.append(calls[idx])
    return {
        "tool_calls": tool_calls,
        "text": "".join(text_buf),
        "finish_reason": finish_reason or "tool_calls",
        "usage": usage,
    }
