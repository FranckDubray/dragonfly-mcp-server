from __future__ import annotations
from typing import Any, Dict, List
import time, random

from .utils import extract_first_json_block
from .prompts_loader import load_system_and_cdc
from ..call_llm import run as call_llm_run  # use internal tool

RETRY_ATTEMPTS = 3
RETRY_DELAY_SEC = 10.0
LLM_TIMEOUT_SEC = 180  # constant internal (handled in call_llm backend)
MAX_CTX_BYTES = 50000  # per-task cap to avoid flooding
MAX_TOKENS_AUDIT = 300  # hard cap per audit call


def _retryable(err_text: str) -> bool:
    e = (err_text or "").lower()
    return any(k in e for k in ("timeout", "429", "rate limit", "5xx", "unavailable", "temporarily"))


def call_model_with_retry(model: str, system: str, messages: List[Dict[str, Any]], max_tokens: int, temperature: float) -> Dict[str, Any]:
    last_err = None
    for i in range(RETRY_ATTEMPTS):
        try:
            res = call_llm_run(message="audit", messages=messages, promptSystem=system, model=model, temperature=temperature, max_tokens=max_tokens, debug=False)
            return res
        except Exception as e:
            last_err = str(e)
            if _retryable(last_err) and i < RETRY_ATTEMPTS - 1:
                delay = RETRY_DELAY_SEC * (0.8 + 0.4 * random.random())
                time.sleep(delay)
                continue
            raise


def run_task(model: str, profile: str, context_pack: Dict[str, Any]) -> Dict[str, Any]:
    try:
        system, cdc = load_system_and_cdc(profile)
    except Exception:
        system, cdc = ("Audit tool MCP — JSON only", f"profile={profile} return JSON findings compact")

    # Add explicit cap hint to CDC
    cdc = cdc + "\nHard cap: return JSON under 300 tokens. Max 10 findings."

    messages: List[Dict[str, Any]] = [{"role": "user", "content": cdc}]

    total = 0
    for ch in context_pack.get("chunks", [])[:10]:
        content = ch.get("content", "")
        if not content:
            continue
        b = len(content.encode("utf-8", errors="ignore"))
        if total + b > MAX_CTX_BYTES:
            break
        messages.append({"role": "user", "content": f"FILE {ch['path']}\n{content}"})
        total += b

    try:
        llm_out = call_model_with_retry(model=model, system=system, messages=messages, max_tokens=MAX_TOKENS_AUDIT, temperature=0.2)
        content = ""
        usage = None
        if isinstance(llm_out, dict):
            content = llm_out.get("content") or ""
            usage = llm_out.get("usage")
        obj = extract_first_json_block(content) or {"status": "invalid_model_output", "findings": []}
        res: Dict[str, Any] = {"model": model, "profile": profile, "report": obj}
        if usage:
            res["usage"] = usage
        return res
    except Exception as e:
        return {"model": model, "profile": profile, "error": str(e), "status": "failed"}
