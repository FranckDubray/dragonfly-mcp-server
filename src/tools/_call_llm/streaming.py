from __future__ import annotations
"""
Streaming utilities for LLM responses (SSE) - Main module
Aggregates text and reconstructs tool_calls in streaming mode.
"""
import json
import logging
from typing import Any, Dict, List, Set
from .streaming_sse import flags, extract_data_str, stats_init
from .streaming_media import collect_media_from_gemini_content, collect_media_from_openai_message_content
from .streaming_fallback import fallback_parse_non_stream_json

LOG = logging.getLogger(__name__)
PREVIEW_MAX = 10


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


def _args_to_str(args: Any) -> str:
    """Normalize arguments to string."""
    if isinstance(args, dict):
        try:
            return json.dumps(args, separators=(",", ":"))
        except Exception:
            return str(args)
    return args if isinstance(args, str) else str(args)


def process_streaming_chunks(response):
    """Aggregate text from SSE stream (simple text generation, no tool_calls)"""
    TRACE, DUMP, DUMP_MAX, INCL_CHOICES = flags()

    headers = {k.lower(): v for k, v in (response.headers or {}).items()}
    ct = (headers.get("content-type") or "").lower()

    thread_id = None
    assistant_message_id = None

    if "text/event-stream" not in ct:
        try:
            obj = response.json()
        except Exception:
            try:
                obj = json.loads(response.text or "{}")
            except Exception:
                obj = {}
        out = fallback_parse_non_stream_json(obj)
        out["sse_stats"] = stats_init()
        out["raw_preview"] = [_trim_str(json.dumps(obj)[:4000], 4000)] if obj else []
        out["response_headers"] = _trim_val(headers, 1000)
        if isinstance(obj, dict):
            thread_id = obj.get("threadId") or obj.get("thread_id")
            assistant_message_id = obj.get("id")
        out["thread_id"] = thread_id
        out["assistant_message_id"] = assistant_message_id
        if DUMP:
            out["raw"] = [_trim_str(json.dumps(obj), 4000)]
        return out

    content = ""
    finish_reason = None
    usage = None
    raw_preview = []
    raw_full = [] if DUMP else None
    sse_stats = stats_init()
    media: List[Dict[str, Any]] = []

    for line_b in response.iter_lines():
        if not line_b:
            sse_stats["empty_lines"] += 1
            continue
        sse_stats["total_lines"] += 1
        line = line_b.decode('utf-8').strip()
        data_str = extract_data_str(line)
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
            choices = chunk.get("choices", [])
            for ch in choices:
                delta = ch.get("delta", {})
                if isinstance(delta.get("content"), str):
                    content += delta["content"]
                    sse_stats["delta_content_bytes"] += len(delta["content"])
                elif isinstance(delta.get("content"), dict):
                    media.extend(collect_media_from_gemini_content(delta["content"]))
                if ch.get("finish_reason"):
                    finish_reason = ch["finish_reason"]
                    sse_stats["final_seen_finish_reason"] = finish_reason
                msg = ch.get("message") or {}
                if isinstance(msg, dict) and isinstance(msg.get("content"), list):
                    media.extend(collect_media_from_openai_message_content(msg["content"]))
            if chunk.get("usage"):
                usage = chunk["usage"]
            if chunk.get("thread_id"):
                thread_id = chunk["thread_id"]
            if chunk.get("id"):
                assistant_message_id = chunk["id"]
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
        "thread_id": thread_id,
        "assistant_message_id": assistant_message_id,
    }
    if media:
        out["media"] = media
    if DUMP:
        out["raw"] = raw_full
    return out


def process_tool_calls_stream(response):
    """Reconstruct tool_calls and capture streamed text.

    De-duplication strategy:
    - Primary source: delta.tool_calls (streaming fragments, concatenated)
    - Secondary source: message.tool_calls (full snapshot in same chunk)
    - A call index is considered "delta-populated" once any argument fragment
      arrives via delta. Once populated, the message snapshot for that index
      is ignored entirely to prevent double-writing.
    - Additionally, call IDs seen in delta are tracked so that message-level
      tool_calls can be matched by id even when index is missing/0.
    """
    TRACE, DUMP, DUMP_MAX, INCL_CHOICES = flags()

    headers = {k.lower(): v for k, v in (response.headers or {}).items()}
    ct = (headers.get("content-type") or "").lower()

    thread_id = None
    assistant_message_id = None

    if "text/event-stream" not in ct:
        try:
            obj = response.json()
        except Exception:
            try:
                obj = json.loads(response.text or "{}")
            except Exception:
                obj = {}
        if isinstance(obj, dict):
            thread_id = obj.get("threadId") or obj.get("thread_id")
            assistant_message_id = obj.get("id")
        fallback = fallback_parse_non_stream_json(obj)
        out = {
            "tool_calls": fallback.get("tool_calls", []),
            "text": fallback.get("content", ""),
            "finish_reason": fallback.get("finish_reason", "stop"),
            "usage": fallback.get("usage"),
            "sse_stats": stats_init(),
            "raw_preview": [_trim_str(json.dumps(obj)[:4000], 4000)] if obj else [],
            "response_headers": _trim_val(headers, 1000),
            "thread_id": thread_id,
            "assistant_message_id": assistant_message_id,
            "provider_preview": [],
        }
        if "media" in fallback:
            out["media"] = fallback["media"]
        if DUMP:
            out["raw"] = [_trim_str(json.dumps(obj), 4000)]
        return out

    # calls[idx] = {"id": ..., "function": {"name": ..., "arguments": ""}}
    calls: Dict[int, Dict[str, Any]] = {}
    # Tracks indices populated via delta stream fragments
    delta_populated_idx: Set[int] = set()
    # Tracks call IDs already seen in delta (for id-based dedup)
    delta_populated_ids: Set[str] = set()

    text_buf: List[str] = []
    finish_reason = None
    usage = None
    raw_preview = []
    raw_full = [] if DUMP else None
    sse_stats = stats_init()
    media: List[Dict[str, Any]] = []

    def _ensure_entry(idx: int) -> Dict[str, Any]:
        return calls.setdefault(idx, {"id": None, "function": {"name": None, "arguments": ""}})

    for line_b in response.iter_lines():
        if not line_b:
            sse_stats["empty_lines"] += 1
            continue
        sse_stats["total_lines"] += 1
        line = line_b.decode('utf-8').strip()
        data_str = extract_data_str(line)
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

        choices = obj.get("choices", [])
        for ch in choices:
            delta = ch.get("delta", {})

            # --- Text content ---
            if isinstance(delta.get("content"), str):
                text_buf.append(delta["content"])
                sse_stats["delta_content_bytes"] += len(delta["content"])
            elif isinstance(delta.get("content"), dict):
                media.extend(collect_media_from_gemini_content(delta["content"]))

            # --- Delta tool_calls (streaming fragments — PRIMARY SOURCE) ---
            for item in delta.get("tool_calls", []) or []:
                idx = item.get("index", 0)
                entry = _ensure_entry(idx)
                if item.get("id"):
                    entry["id"] = item["id"]
                    delta_populated_ids.add(item["id"])
                fn = item.get("function") or {}
                if fn.get("name"):
                    entry["function"]["name"] = fn["name"]
                if fn.get("arguments"):
                    entry["function"]["arguments"] += _args_to_str(fn["arguments"])
                    delta_populated_idx.add(idx)

            # --- Alternative delta formats (some providers) ---
            if ("tool_calls_index" in delta) or ("function_name" in delta) or ("arguments" in delta):
                idx = delta.get("tool_calls_index", 0)
                entry = _ensure_entry(idx)
                if delta.get("function_name"):
                    entry["function"]["name"] = delta.get("function_name")
                if delta.get("arguments") is not None:
                    entry["function"]["arguments"] += _args_to_str(delta.get("arguments"))
                    delta_populated_idx.add(idx)

            # --- function_call (legacy OpenAI format) ---
            fnc = delta.get("function_call") or {}
            if fnc:
                entry = _ensure_entry(0)
                if fnc.get("name"):
                    entry["function"]["name"] = fnc["name"]
                if fnc.get("arguments"):
                    entry["function"]["arguments"] += _args_to_str(fnc["arguments"])
                delta_populated_idx.add(0)

            # --- message.tool_calls (full snapshot — SECONDARY SOURCE) ---
            # Only used when delta did NOT already populate the call.
            # Deduplication: skip by index OR by call id (handles gpt-5.2 which
            # sends both delta and message in the same chunk with index missing).
            msg = ch.get("message") or {}
            for item in (msg.get("tool_calls") or []) if isinstance(msg.get("tool_calls"), list) else []:
                idx = item.get("index", 0)
                call_id = item.get("id") or ""

                # Skip if already populated via delta (by index or by id)
                if idx in delta_populated_idx:
                    continue
                if call_id and call_id in delta_populated_ids:
                    continue

                entry = _ensure_entry(idx)
                if call_id:
                    entry["id"] = call_id
                fn = item.get("function") or {}
                if fn.get("name"):
                    entry["function"]["name"] = fn["name"]
                # Only write arguments if not already set
                if fn.get("arguments") and not entry["function"]["arguments"]:
                    entry["function"]["arguments"] = _args_to_str(fn["arguments"])

            # --- message.function_call (legacy, full) ---
            fnc_msg = (msg.get("function_call") or {}) if isinstance(msg, dict) else {}
            if fnc_msg and 0 not in delta_populated_idx:
                entry = _ensure_entry(0)
                if fnc_msg.get("name"):
                    entry["function"]["name"] = fnc_msg["name"]
                if fnc_msg.get("arguments") and not entry["function"]["arguments"]:
                    entry["function"]["arguments"] = _args_to_str(fnc_msg["arguments"])

            # --- Media from message content ---
            if isinstance(msg, dict) and isinstance(msg.get("content"), list):
                media.extend(collect_media_from_openai_message_content(msg["content"]))

            if ch.get("finish_reason"):
                finish_reason = ch["finish_reason"]
                sse_stats["final_seen_finish_reason"] = finish_reason

        if obj.get("usage"):
            usage = obj["usage"]
        if obj.get("thread_id"):
            thread_id = obj["thread_id"]
        if obj.get("id"):
            assistant_message_id = obj["id"]

    tool_calls = [calls[idx] for idx in sorted(calls.keys())]
    out = {
        "tool_calls": tool_calls,
        "text": "".join(text_buf),
        "finish_reason": finish_reason or "tool_calls",
        "usage": usage,
        "sse_stats": sse_stats,
        "raw_preview": raw_preview,
        "response_headers": _trim_val(headers, 1000),
        "thread_id": thread_id,
        "assistant_message_id": assistant_message_id,
        "provider_preview": [],
    }
    if media:
        out["media"] = media
    if TRACE:
        out["trace"] = []
    if DUMP:
        out["raw"] = raw_full
    return out
