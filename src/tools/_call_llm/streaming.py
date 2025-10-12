
"""
Streaming utilities for LLM responses (SSE)
- Aggregates text and reconstructs tool_calls in streaming mode.
- Always returns rich debug fields so callers can understand issues when no tool_calls are emitted.
- Extended: extract non-text multimodal parts (images/files) from provider-specific content structures
  such as Google Gemini content.parts[].inline_data / fileUri and OpenAI-style message.content[].image_url.
- Fallback: if the server does NOT stream (content-type != text/event-stream), parse the JSON body once
  and extract choices/message/content/tool_calls/usage accordingly.
"""
import json
import logging
import os
from typing import Any, Dict, List

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


# -------- Multimodal extraction helpers (URLs / inline images) ---------

def _collect_media_from_gemini_content(content: Any) -> List[Dict[str, Any]]:
    media: List[Dict[str, Any]] = []
    try:
        parts = None
        if isinstance(content, dict) and isinstance(content.get("parts"), list):
            parts = content["parts"]
        elif isinstance(content, list):
            parts = content
        if not parts:
            return media
        for part in parts:
            if not isinstance(part, dict):
                continue
            mime = part.get("mime_type") or part.get("mimeType")
            # inline_data (base64)
            inline = part.get("inline_data") or part.get("inlineData")
            if isinstance(inline, dict) and inline.get("data"):
                media.append({
                    "kind": "inline",
                    "mime_type": mime,
                    "data_base64": _trim_str(inline.get("data"), 100000),
                })
                continue
            # fileUri / file_uri
            file_uri = part.get("fileUri") or part.get("file_uri")
            if isinstance(file_uri, str):
                media.append({
                    "kind": "url",
                    "mime_type": mime,
                    "url": file_uri,
                })
                continue
            # file_data may contain {fileUri: ...}
            file_data = part.get("file_data") or part.get("fileData")
            if isinstance(file_data, dict):
                fu = file_data.get("fileUri") or file_data.get("file_uri")
                if isinstance(fu, str):
                    media.append({
                        "kind": "url",
                        "mime_type": mime or file_data.get("mime_type") or file_data.get("mimeType"),
                        "url": fu,
                    })
                    continue
            # generic url / image_url
            image_url = part.get("image_url")
            if isinstance(image_url, str):
                media.append({"kind": "url", "mime_type": mime, "url": image_url})
                continue
            if isinstance(image_url, dict) and isinstance(image_url.get("url"), str):
                media.append({"kind": "url", "mime_type": mime, "url": image_url["url"]})
                continue
            if isinstance(part.get("url"), str):
                media.append({"kind": "url", "mime_type": mime, "url": part.get("url")})
                continue
    except Exception:
        pass
    return media


def _collect_media_from_openai_message_content(content: Any) -> List[Dict[str, Any]]:
    media: List[Dict[str, Any]] = []
    try:
        if isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue
                typ = (item.get("type") or "").lower()
                # image_url can be string or object {url: ...}
                if "image_url" in item:
                    v = item.get("image_url")
                    if isinstance(v, str):
                        media.append({"kind": "url", "url": v})
                    elif isinstance(v, dict) and isinstance(v.get("url"), str):
                        media.append({"kind": "url", "url": v["url"]})
                # generic url
                elif isinstance(item.get("url"), str) and typ in ("image", "image_url", "file", "media"):
                    media.append({"kind": "url", "url": item["url"]})
    except Exception:
        pass
    return media


# -------- Non-SSE fallback helpers ---------

def _extract_text_from_message_content(content: Any) -> str:
    out = ""
    try:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    if part.get("type") == "text" and isinstance(part.get("text"), str):
                        out += part["text"]
    except Exception:
        pass
    return out


def _fallback_parse_non_stream_json(obj: Dict[str, Any]) -> Dict[str, Any]:
    # Some providers wrap under {response: {...}}
    if "response" in obj and "choices" not in obj:
        try:
            obj = obj["response"]
        except Exception:
            pass
    content = ""
    finish_reason = None
    usage = obj.get("usage")
    media: List[Dict[str, Any]] = []
    tool_calls: List[Dict[str, Any]] = []

    try:
        choices = obj.get("choices") or []
        for ch in choices:
            # text
            msg = ch.get("message") or {}
            if isinstance(msg, dict) and "content" in msg:
                content += _extract_text_from_message_content(msg.get("content"))
                # collect media if present in message content (OpenAI-style)
                media.extend(_collect_media_from_openai_message_content(msg.get("content")))
            # tool_calls
            tcs = (msg.get("tool_calls") or []) if isinstance(msg, dict) else []
            for item in tcs:
                if not isinstance(item, dict):
                    continue
                fn = item.get("function") or {}
                name = fn.get("name")
                args = fn.get("arguments")
                if isinstance(args, dict):
                    try:
                        args = json.dumps(args, separators=(",", ":"))
                    except Exception:
                        args = str(args)
                tool_calls.append({
                    "id": item.get("id"),
                    "function": {"name": name, "arguments": args or ""}
                })
            # finish reason
            if ch.get("finish_reason"):
                finish_reason = ch.get("finish_reason")
    except Exception:
        pass

    out: Dict[str, Any] = {
        "content": content,
        "finish_reason": finish_reason or "stop",
        "usage": usage,
        "response_headers": {},
    }
    if media:
        out["media"] = media
    if tool_calls:
        out["tool_calls"] = tool_calls
    return out


def process_streaming_chunks(response):
    """
    Aggregate text from SSE stream.
    Returns: {
      "content": str, "finish_reason": str, "usage": dict|None,
      "sse_stats": dict, "raw_preview": list,
      (optional) "raw": list, "response_headers": dict,
      (optional) "media": list  # extracted non-text parts (urls / inline)
    }
    """
    TRACE, DUMP, DUMP_MAX, INCL_CHOICES = _flags()

    headers = {k.lower(): v for k, v in (response.headers or {}).items()}
    ct = (headers.get("content-type") or "").lower()
    if "text/event-stream" not in ct:
        # Non-SSE fallback: parse JSON body once
        try:
            obj = response.json()
        except Exception:
            try:
                obj = json.loads(response.text or "{}")
            except Exception:
                obj = {}
        out = _fallback_parse_non_stream_json(obj)
        out["sse_stats"] = _stats_init()
        out["raw_preview"] = [_trim_str(json.dumps(obj)[:4000], 4000)] if obj else []
        out["response_headers"] = _trim_val(headers, 1000)
        if DUMP:
            out["raw"] = [_trim_str(json.dumps(obj), 4000)]
        return out

    content = ""
    finish_reason = None
    usage = None
    raw_preview = []
    raw_full = [] if DUMP else None
    sse_stats = _stats_init()
    media: List[Dict[str, Any]] = []

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
            choices = chunk.get("choices", [])
            for ch in choices:
                delta = ch.get("delta", {})
                if isinstance(delta.get("content"), str):
                    content += delta["content"]
                    sse_stats["delta_content_bytes"] += len(delta["content"])
                elif isinstance(delta.get("content"), dict):
                    media.extend(_collect_media_from_gemini_content(delta["content"]))
                if ch.get("finish_reason"):
                    finish_reason = ch["finish_reason"]
                    sse_stats["final_seen_finish_reason"] = finish_reason
                msg = ch.get("message") or {}
                if isinstance(msg, dict) and isinstance(msg.get("content"), list):
                    media.extend(_collect_media_from_openai_message_content(msg["content"]))
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
    if media:
        out["media"] = media
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
      (optional) trace, raw, provider_preview,
      (optional) "media": list  # extracted non-text parts (urls / inline)
    }
    """
    TRACE, DUMP, DUMP_MAX, INCL_CHOICES = _flags()

    headers = {k.lower(): v for k, v in (response.headers or {}).items()}
    ct = (headers.get("content-type") or "").lower()
    if "text/event-stream" not in ct:
        # Non-SSE fallback: parse JSON body once
        try:
            obj = response.json()
        except Exception:
            try:
                obj = json.loads(response.text or "{}")
            except Exception:
                obj = {}
        fallback = _fallback_parse_non_stream_json(obj)
        out = {
            "tool_calls": fallback.get("tool_calls", []),
            "text": fallback.get("content", ""),
            "finish_reason": fallback.get("finish_reason", "stop"),
            "usage": fallback.get("usage"),
            "sse_stats": _stats_init(),
            "raw_preview": [_trim_str(json.dumps(obj)[:4000], 4000)] if obj else [],
            "response_headers": _trim_val(headers, 1000),
            "provider_preview": [],
        }
        if "media" in fallback:
            out["media"] = fallback["media"]
        if DUMP:
            out["raw"] = [_trim_str(json.dumps(obj), 4000)]
        return out

    calls: Dict[int, Dict[str, Any]] = {}
    text_buf: List[str] = []
    finish_reason = None
    usage = None
    trace = [] if TRACE else None
    raw_preview = []
    raw_full = [] if DUMP else None
    sse_stats = _stats_init()
    provider_preview = []  # list of partial provider-specific accumulators per index
    media: List[Dict[str, Any]] = []

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
        choices = obj.get("choices", [])
        for ch in choices:
            delta = ch.get("delta", {})
            if isinstance(delta.get("content"), str):
                text_buf.append(delta["content"])
                sse_stats["delta_content_bytes"] += len(delta["content"])
            elif isinstance(delta.get("content"), dict):
                media.extend(_collect_media_from_gemini_content(delta["content"]))
            for item in delta.get("tool_calls", []) or []:
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
            if ("tool_calls_index" in delta) or ("function_name" in delta) or ("arguments" in delta):
                idx = delta.get("tool_calls_index", 0)
                entry = _ensure_entry(idx)
                if delta.get("function_name"):
                    entry["function"]["name"] = delta.get("function_name")
                if delta.get("arguments") is not None:
                    entry["function"]["arguments"] += delta.get("arguments")
            fnc = delta.get("function_call") or {}
            if fnc:
                entry = _ensure_entry(0)
                if fnc.get("name"):
                    entry["function"]["name"] = fnc["name"]
                if fnc.get("arguments"):
                    entry["function"]["arguments"] += fnc["arguments"]
            msg = ch.get("message") or {}
            for item in (msg.get("tool_calls") or []) if isinstance(msg.get("tool_calls"), list) else []:
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
            fnc_msg = (msg.get("function_call") or {}) if isinstance(msg, dict) else {}
            if fnc_msg:
                entry = _ensure_entry(0)
                if fnc_msg.get("name"):
                    entry["function"]["name"] = fnc_msg["name"]
                if fnc_msg.get("arguments") and not entry["function"]["arguments"]:
                    entry["function"]["arguments"] = fnc_msg["arguments"]
            if isinstance(msg, dict) and isinstance(msg.get("content"), list):
                media.extend(_collect_media_from_openai_message_content(msg["content"]))
            if ch.get("finish_reason"):
                finish_reason = ch["finish_reason"]
                sse_stats["final_seen_finish_reason"] = finish_reason
        if obj.get("usage"):
            usage = obj["usage"]
    tool_calls = [calls[idx] for idx in sorted(calls.keys())]
    out = {
        "tool_calls": tool_calls,
        "text": "".join(text_buf),
        "finish_reason": finish_reason or "tool_calls",
        "usage": usage,
        "sse_stats": sse_stats,
        "raw_preview": raw_preview,
        "response_headers": _trim_val(headers, 1000),
        "provider_preview": [],
    }
    if media:
        out["media"] = media
    if TRACE:
        out["trace"] = []
    if DUMP:
        out["raw"] = raw_full
    return out
