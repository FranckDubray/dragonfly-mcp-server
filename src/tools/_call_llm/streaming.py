"""
Streaming utilities for LLM responses (SSE)
- Supports both text aggregation and tool_calls reconstruction in streaming mode.
- Optional trace mode: set env LLM_STREAM_TRACE=1 to include a per-chunk trace for debugging.
- Optional raw dump: set env LLM_STREAM_DUMP=1 (or 'all') to capture raw SSE JSON lines
  up to LLM_STREAM_DUMP_MAX (default 10; if 'all' then 10000).
"""
import json
import logging
import os

LOG = logging.getLogger(__name__)

TRACE = os.getenv("LLM_STREAM_TRACE", "").strip().lower() in ("1","true","yes","on","debug")
_dump_mode = os.getenv("LLM_STREAM_DUMP", "").strip().lower()
DUMP = _dump_mode in ("1","true","yes","on","debug","all")
if _dump_mode == "all":
    DUMP_MAX = 10000
else:
    try:
        DUMP_MAX = int(os.getenv("LLM_STREAM_DUMP_MAX", "10"))
    except Exception:
        DUMP_MAX = 10


def _trim(s: str, limit: int = 4000) -> str:
    try:
        if isinstance(s, str) and len(s) > limit:
            return s[:limit] + f"... (+{len(s)-limit} bytes)"
    except Exception:
        pass
    return s


def process_streaming_chunks(response):
    """
    Process streaming response and return aggregated text content.
    Expects Server-Sent Events with lines starting by 'data: '.
    Returns: {"content": str, "finish_reason": str, "usage": dict|None, "raw": list|None}
    """
    content = ""
    finish_reason = None
    usage = None
    raw = [] if DUMP else None
    for line in response.iter_lines():
        if not line:
            continue
        line = line.decode('utf-8').strip()
        if not line.startswith('data: '):
            continue
        data_str = line[6:]
        if data_str == '[DONE]':
            break
        if DUMP and len(raw) < DUMP_MAX:
            raw.append(_trim(data_str, 4000))
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
    out = {"content": content, "finish_reason": finish_reason or "stop", "usage": usage}
    if DUMP:
        out["raw"] = raw
    return out


def process_tool_calls_stream(response):
    """
    Consume SSE stream and reconstruct tool_calls (OpenAI streaming format) and any text fragments.
    Returns: {
      "tool_calls": [ {"id": str|None, "function": {"name": str|None, "arguments": str}}, ...],
      "text": str,  # any assistant text streamed (if present)
      "finish_reason": str,
      "usage": dict|None,
      "trace": list|None,  # optional per-chunk trace if LLM_STREAM_TRACE=1
      "raw": list|None     # optional raw JSON lines if LLM_STREAM_DUMP=1
    }
    """
    # index -> entry {"id":..., "function": {"name":..., "arguments": str}}
    calls = {}
    text_buf = []
    finish_reason = None
    usage = None
    trace = [] if TRACE else None
    raw = [] if DUMP else None

    for raw_line in response.iter_lines():
        if not raw_line:
            continue
        line = raw_line.decode('utf-8').strip()
        if not line.startswith('data: '):
            continue
        data_str = line[6:]
        if data_str == '[DONE]':
            break
        if DUMP and len(raw) < DUMP_MAX:
            raw.append(_trim(data_str, 4000))
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
        choice0 = choices[0] or {}
        delta = choice0.get("delta", {})
        # Aggregate text if any
        if delta.get("content"):
            text_buf.append(delta["content"])
        # Aggregate tool_calls fragments from delta.tool_calls
        d_tc = delta.get("tool_calls", []) or []
        d_tc_count = 0
        for item in d_tc:
            idx = item.get("index", 0)
            entry = calls.setdefault(idx, {"id": None, "function": {"name": None, "arguments": ""}})
            if item.get("id"):
                entry["id"] = item["id"]
            fn = item.get("function") or {}
            if fn.get("name"):
                entry["function"]["name"] = fn["name"]
            if fn.get("arguments"):
                args = fn["arguments"]
                if isinstance(args, dict):
                    try:
                        args = json.dumps(args, separators=(",", ":"))
                    except Exception:
                        args = str(args)
                entry["function"]["arguments"] += args
            d_tc_count += 1
        # Some providers send final tool_calls under message.tool_calls (not delta)
        msg = choice0.get("message") or {}
        m_tc = (msg.get("tool_calls") or []) if isinstance(msg.get("tool_calls"), list) else []
        m_tc_count = 0
        for item in m_tc:
            idx = item.get("index", 0)
            entry = calls.setdefault(idx, {"id": None, "function": {"name": None, "arguments": ""}})
            if item.get("id"):
                entry["id"] = item["id"]
            fn = item.get("function") or {}
            if fn.get("name"):
                entry["function"]["name"] = fn["name"]
            if fn.get("arguments") and not entry["function"]["arguments"]:
                args = fn["arguments"]
                if isinstance(args, dict):
                    try:
                        args = json.dumps(args, separators=(",", ":"))
                    except Exception:
                        args = str(args)
                entry["function"]["arguments"] = args
            m_tc_count += 1
        # Finish reason
        if choice0.get("finish_reason"):
            finish_reason = choice0["finish_reason"]
        # Usage if present
        if obj.get("usage"):
            usage = obj["usage"]
        # Trace
        if TRACE:
            trace.append({
                "delta_has_tool_calls": bool(d_tc),
                "delta_tool_calls_count": d_tc_count,
                "message_tool_calls_count": m_tc_count,
                "delta_has_content": bool(delta.get("content")),
                "finish_reason_line": choice0.get("finish_reason"),
            })

    # Order calls by index
    tool_calls = []
    for idx in sorted(calls.keys()):
        tool_calls.append(calls[idx])
    out = {
        "tool_calls": tool_calls,
        "text": "".join(text_buf),
        "finish_reason": finish_reason or "tool_calls",
        "usage": usage,
    }
    if TRACE:
        out["trace"] = trace
    if DUMP:
        out["raw"] = raw
    return out
