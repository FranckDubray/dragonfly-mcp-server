"""
Streaming utilities for LLM responses (SSE)
- Aggregates text and reconstructs tool_calls in streaming mode.
- Always returns rich debug fields so callers can understand issues when no tool_calls are emitted.
"""
import json
import logging
import os
from typing import Any, Dict

LOG = logging.getLogger(__name__)

PREVIEW_MAX = 10


def _flags():
    trace = os.getenv("LLM_STREAM_TRACE", "").strip().lower() in ("1", "true", "yes", "on", "debug")
    dump_mode = os.getenv("LLM_STREAM_DUMP", "").strip().lower()
    dump = dump_mode in ("1", "true", "yes", "on", "debug", "all")
    if dump_mode == "all":
        dump_max = 10000
    else:
        try:
            dump_max = int(os.getenv("LLM_STREAM_DUMP_MAX", "50"))
        except Exception:
            dump_max = 50
    incl_choices = os.getenv("LLM_STREAM_INCLUDE_CHOICES", "").strip().lower() in ("1", "true", "yes", "on", "debug")
    return trace, dump, dump_max, incl_choices


def _trim_str(s: str, limit: int = 4000) -> str:
    try:
        if isinstance(s, str) and len(s) > limit:
            return s[:limit] + f"... (+{len(s)-limit} bytes)"
    except Exception:
        pass
    return s


def _trim_val(x: Any, limit: int = 2000) -> Any:
    try:
        if isinstance(x, dict):
            return {k: _trim_val(v, limit) for k, v in x.items()}
        if isinstance(x, list):
            return [_trim_val(v, limit) for v in x]
        if isinstance(x, str):
            return _trim_str(x, limit)
    except Exception:
        return x
    return x


def _stats_init() -> Dict[str, Any]:
    return dict(
        total_lines=0,
        parsed_lines=0,
        non_data_lines=0,
        empty_lines=0,
        json_errors=0,
        done=False,
        choices_total=0,
        choices_with_delta=0,
        delta_tool_calls_total=0,
        message_tool_calls_total=0,
        delta_function_call_total=0,
        message_function_call_total=0,
        provider_tool_calls_total=0,
        delta_content_bytes=0,
        ids_seen=[],
        final_seen_finish_reason=None,
    )


def _extract_data_str(line: str) -> str | None:
    """Accept both 'data: {...}' and 'data:{...}' and trim space."""
    if not line.startswith('data:'):
        return None
    return line[5:].lstrip()


def process_streaming_chunks(response):
    """
    Aggregate text from SSE stream.
    Returns: {
      "content": str, "finish_reason": str, "usage": dict|None,
      "sse_stats": dict, "raw_preview": list,
      (optional) "raw": list, "response_headers": dict
    }
    """
    TRACE, DUMP, DUMP_MAX, INCL_CHOICES = _flags()
    content = ""
    finish_reason = None
    usage = None
    raw_preview = []
    raw_full = [] if DUMP else None
    sse_stats = _stats_init()

    headers = {k.lower(): v for k, v in (response.headers or {}).items()}

    for line_b in response.iter_lines():
        if not line_b:
            sse_stats["empty_lines"] += 1
            continue
        sse_stats["total_lines"] += 1
        line = line_b.decode('utf-8').strip()
        data_str = _extract_data_str(line)
        if data_str is None:
            sse_stats["non_data_lines"] += 1
            continue
        if data_str == '[DONE]':
            sse_stats["done"] = True
            break
        if len(raw_preview) < PREVIEW_MAX:
            raw_preview.append(_trim_str(data_str, 4000))
        if DUMP and len(raw_full) < DUMP_MAX:
            raw_full.append(_trim_str(data_str, 4000))
        try:
            chunk = json.loads(data_str)
            sse_stats["parsed_lines"] += 1
            if "response" in chunk and "choices" not in chunk:
                chunk = chunk["response"]
            if chunk.get("id"):
                ids = sse_stats["ids_seen"]
                if chunk["id"] not in ids:
                    ids.append(chunk["id"])
            choices = chunk.get("choices", [])
            sse_stats["choices_total"] += len(choices)
            for ch in choices:
                delta = ch.get("delta", {})
                if delta:
                    sse_stats["choices_with_delta"] += 1
                if delta.get("content"):
                    content += delta["content"]
                    sse_stats["delta_content_bytes"] += len(delta["content"])
                if ch.get("finish_reason"):
                    finish_reason = ch["finish_reason"]
                    sse_stats["final_seen_finish_reason"] = finish_reason
            if chunk.get("usage"):
                usage = chunk["usage"]
        except Exception:
            sse_stats["json_errors"] += 1
            continue
    out = {
        "content": content,
        "finish_reason": finish_reason or "stop",
        "usage": usage,
        "sse_stats": sse_stats,
        "raw_preview": raw_preview,
        "response_headers": _trim_val(headers, 1000),
    }
    if DUMP:
        out["raw"] = raw_full
    return out


def process_tool_calls_stream(response):
    """
    Reconstruct tool_calls and capture any streamed text.
    Returns: {
      "tool_calls": [ {"id": str|None, "function": {"name": str|None, "arguments": str}}, ...],
      "text": str, "finish_reason": str, "usage": dict|None,
      "sse_stats": dict, "raw_preview": list, "response_headers": dict,
      (optional) trace, raw, provider_preview
    }
    """
    TRACE, DUMP, DUMP_MAX, INCL_CHOICES = _flags()

    calls: Dict[int, Dict[str, Any]] = {}
    text_buf = []
    finish_reason = None
    usage = None
    trace = [] if TRACE else None
    raw_preview = []
    raw_full = [] if DUMP else None
    sse_stats = _stats_init()
    provider_preview = []  # list of partial provider-specific accumulators per index

    headers = {k.lower(): v for k, v in (response.headers or {}).items()}

    def _ensure_entry(idx: int):
        return calls.setdefault(idx, {"id": None, "function": {"name": None, "arguments": ""}})

    for line_b in response.iter_lines():
        if not line_b:
            sse_stats["empty_lines"] += 1
            continue
        sse_stats["total_lines"] += 1
        line = line_b.decode('utf-8').strip()
        data_str = _extract_data_str(line)
        if data_str is None:
            sse_stats["non_data_lines"] += 1
            continue
        if data_str == '[DONE]':
            sse_stats["done"] = True
            break
        if len(raw_preview) < PREVIEW_MAX:
            raw_preview.append(_trim_str(data_str, 4000))
        if DUMP and len(raw_full) < DUMP_MAX:
            raw_full.append(_trim_str(data_str, 4000))
        try:
            obj = json.loads(data_str)
        except Exception:
            sse_stats["json_errors"] += 1
            continue
        sse_stats["parsed_lines"] += 1
        if "response" in obj and "choices" not in obj:
            obj = obj["response"]
        if obj.get("id"):
            ids = sse_stats["ids_seen"]
            if obj["id"] not in ids:
                ids.append(obj["id"])
        choices = obj.get("choices", [])
        sse_stats["choices_total"] += len(choices)
        for ch in choices:
            delta = ch.get("delta", {})
            if delta:
                sse_stats["choices_with_delta"] += 1
            # 1) Text deltas
            if delta.get("content"):
                text_buf.append(delta["content"])
                sse_stats["delta_content_bytes"] += len(delta["content"])
            # 2) tool_calls fragments in delta (OpenAI tools)
            for item in delta.get("tool_calls", []) or []:
                sse_stats["delta_tool_calls_total"] += 1
                idx = item.get("index", 0)
                entry = _ensure_entry(idx)
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
            # 2b) PROVIDER-SPECIFIC deltas (function_name/arguments/tool_calls_index/tool_calls_type)
            if ("tool_calls_index" in delta) or ("function_name" in delta) or ("arguments" in delta):
                sse_stats["provider_tool_calls_total"] += 1
                idx = delta.get("tool_calls_index", 0)
                entry = _ensure_entry(idx)
                prov = {"index": idx}
                if delta.get("tool_calls_type") and not entry.get("id"):
                    entry["id"] = delta.get("tool_calls_type")
                prov["id"] = entry.get("id")
                if delta.get("function_name"):
                    entry["function"]["name"] = delta.get("function_name")
                prov["name"] = entry["function"].get("name")
                if delta.get("arguments") is not None:
                    entry["function"]["arguments"] += delta.get("arguments")
                prov["arguments_len"] = len(entry["function"]["arguments"])
                prov["arguments_preview"] = _trim_str(entry["function"]["arguments"], 120)
                provider_preview.append(prov)
            # 3) function_call legacy
            fnc = delta.get("function_call") or {}
            if fnc:
                sse_stats["delta_function_call_total"] += 1
                entry = _ensure_entry(0)
                if fnc.get("name"):
                    entry["function"]["name"] = fnc["name"]
                if fnc.get("arguments"):
                    entry["function"]["arguments"] += fnc["arguments"]
            # 4) message.tool_calls
            msg = ch.get("message") or {}
            for item in (msg.get("tool_calls") or []) if isinstance(msg.get("tool_calls"), list) else []:
                sse_stats["message_tool_calls_total"] += 1
                idx = item.get("index", 0)
                entry = _ensure_entry(idx)
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
            # 5) message.function_call
            fnc_msg = (msg.get("function_call") or {}) if isinstance(msg, dict) else {}
            if fnc_msg:
                sse_stats["message_function_call_total"] += 1
                entry = _ensure_entry(0)
                if fnc_msg.get("name"):
                    entry["function"]["name"] = fnc_msg["name"]
                if fnc_msg.get("arguments") and not entry["function"]["arguments"]:
                    entry["function"]["arguments"] = fnc_msg["arguments"]
            # finish
            if ch.get("finish_reason"):
                finish_reason = ch["finish_reason"]
                sse_stats["final_seen_finish_reason"] = finish_reason
        if obj.get("usage"):
            usage = obj["usage"]
        if TRACE:
            trace_item: Dict[str, Any] = {
                "choices_in_chunk": len(choices),
                "finish_reason_line": choices[0].get("finish_reason") if choices else None,
            }
            if INCL_CHOICES:
                trace_item["choices"] = _trim_val(choices, 1000)
            trace.append(trace_item)

    tool_calls = [calls[idx] for idx in sorted(calls.keys())]
    out = {
        "tool_calls": tool_calls,
        "text": "".join(text_buf),
        "finish_reason": finish_reason or "tool_calls",
        "usage": usage,
        "sse_stats": sse_stats,
        "raw_preview": raw_preview,
        "response_headers": _trim_val(headers, 1000),
        "provider_preview": provider_preview[-PREVIEW_MAX:],
    }
    if TRACE:
        out["trace"] = trace
    if DUMP:
        out["raw"] = raw_full
    return out
