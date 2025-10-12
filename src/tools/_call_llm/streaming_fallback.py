"""
Non-SSE fallback: parse JSON body once when content-type != text/event-stream
"""
import json
from typing import Any, Dict, List
from .streaming_media import collect_media_from_openai_message_content


def extract_text_from_message_content(content: Any) -> str:
    """Extract text from message.content (string or array of parts)"""
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


def fallback_parse_non_stream_json(obj: Dict[str, Any]) -> Dict[str, Any]:
    """Parse non-streaming JSON response (no SSE)"""
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
                content += extract_text_from_message_content(msg.get("content"))
                # collect media if present in message content (OpenAI-style)
                media.extend(collect_media_from_openai_message_content(msg.get("content")))
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
