from typing import Any, Dict, List
from ._call_llm.core import execute_call_llm
import os
from ._call_llm.file_utils import _file_to_data_url, _image_part_from_url
import traceback

# Keep DOCS_ABS_ROOT behavior in one place
DOCS_ABS_ROOT = os.getenv("DOCS_ABS_ROOT")

def run(operation: str = "run", **params) -> Dict[str, Any]:
    try:
        debug = bool(params.get("debug"))
        if not params.get("model"):
            out = {"error": "Missing required parameter: model"}
            if debug:
                out["debug"] = {"stage": "pre", "params_keys": list(params.keys())}
            return out

        messages = params.pop("messages", None)
        image_urls = params.pop("image_urls", None) or []
        image_files = params.pop("image_files", None) or []
        msg = params.pop("message", None)

        debug_info: Dict[str, Any] = {"images": {"files": [], "urls": []}, "docs_root": DOCS_ABS_ROOT} if debug else {}

        if not messages:
            if not msg:
                out = {"error": "Missing required parameter: message"}
                if debug:
                    out["debug"] = {"stage": "pre", "hint": "message_required_when_messages_absent"}
                return out
            parts: List[Dict[str, Any]] = []
            if isinstance(msg, str) and msg.strip():
                parts.append({"type": "text", "text": msg})
            try:
                max_img = int(os.getenv("LLM_MAX_IMAGE_COUNT", "4"))
            except Exception:
                max_img = 4
            total_imgs = len(image_urls) + len(image_files)
            if total_imgs > max_img:
                out = {"error": f"Too many images: {total_imgs} > {max_img} (LLM_MAX_IMAGE_COUNT)."}
                if debug:
                    out["debug"] = {"stage": "limit", "image_urls_count": len(image_urls), "image_files_count": len(image_files), "max_img": max_img}
                return out
            for u in image_urls:
                if isinstance(u, str) and u.strip():
                    parts.append(_image_part_from_url(u))
                    if debug:
                        debug_info["images"]["urls"].append({"url": u})
            for p in image_files:
                if not isinstance(p, str) or not p.strip():
                    if debug:
                        debug_info["images"]["files"].append({"path": p, "skipped": True, "reason": "empty_or_invalid"})
                    continue
                data_url, diag = _file_to_data_url(p)
                if not data_url:
                    out = {"error": f"Image file not allowed/too large/unreadable: {p}. Allowed root: {os.getenv('DOCS_ABS_ROOT','<project>/docs')}/"}
                    if debug:
                        debug_info["images"]["files"].append({"path": p, "ok": False, "diag": diag})
                        out["debug"] = debug_info
                    return out
                parts.append(_image_part_from_url(data_url))
                if debug:
                    debug_info["images"]["files"].append({"path": p, "ok": True, "diag": diag})
            if not parts:
                out = {"error": "No valid content built from 'message'/'image_urls'/'image_files'."}
                if debug:
                    out["debug"] = debug_info
                return out
            messages = [{"role": "user", "content": parts}]

        model = params.pop("model")
        max_tokens = params.pop("max_tokens", None)
        tool_names = params.pop("tool_names", None)
        promptSystem = params.pop("promptSystem", None)

        result = execute_call_llm(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            tool_names=tool_names,
            promptSystem=promptSystem,
            debug=debug,
        )
        if debug and isinstance(result, dict):
            if "debug" in result and isinstance(result["debug"], dict):
                result["debug"].setdefault("call_llm_tool", {})
                result["debug"]["call_llm_tool"].update(debug_info)
            else:
                result["debug"] = {"call_llm_tool": debug_info}
        return result
    except Exception as e:
        return {
            "error": f"call_llm failed: {e}",
            "traceback": traceback.format_exc(limit=3),
            "hint": "Search for 'tool_Dict' in _call_llm modules; ensure server reloaded tools.",
        }


def spec() -> Dict[str, Any]:
    import json, os
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'call_llm.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)
