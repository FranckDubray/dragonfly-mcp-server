
from __future__ import annotations
from typing import Any, Dict

VALID_MODELS = {
    "gpt-5",
    "claude-sonnet-4-5-20250929",
    "gpt-5-mini",
    "gemini-2.5-pro",
}

# Constantes internes (pas exposées en params)
LLM_TIMEOUT_SEC = 180
LLM_MAX_CONCURRENCY = 8  # augmenté à 8
LLM_MAX_CONCURRENCY_PER_MODEL = 2
MAX_BYTES_PER_FILE = 65536
MAX_TOTAL_CONTEXT_BYTES = 200000
LLM_TOP_N = 10
DEFAULT_PROFILE_MODE = "auto"  # hybride: 4x combined + 4x profils
DEFAULT_MODELS = [
    "gpt-5",
    "claude-sonnet-4-5-20250929",
    "gpt-5-mini",
    "gemini-2.5-pro",
]


def _unique_preserve_order(seq: list[str]) -> list[str]:
    seen = set()
    out: list[str] = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def validate_params(p: Dict[str, Any]) -> Dict[str, Any]:
    op = p.get("operation")
    if op != "audit_tool":
        raise ValueError("invalid_parameters: operation must be 'audit_tool'")

    tool_name = p.get("tool_name")
    if not tool_name or not isinstance(tool_name, str):
        raise ValueError("invalid_parameters: missing tool_name")

    # models: allow 1..4, unique, known models only
    raw_models = p.get("models")
    if raw_models is None:
        models = DEFAULT_MODELS
    else:
        if not isinstance(raw_models, list) or not all(isinstance(m, str) for m in raw_models):
            raise ValueError("invalid_parameters: models must be an array of strings")
        models = _unique_preserve_order(raw_models)
        if len(models) < 1:
            raise ValueError("invalid_parameters: at least 1 model is required")
        if len(models) > 4:
            raise ValueError("invalid_parameters: at most 4 models are allowed")
    for m in models:
        if m not in VALID_MODELS:
            raise ValueError(f"invalid_parameters: unknown model '{m}'")

    # fuser_model: default = first provided model, fallback to 'gpt-5'
    fuser_model = p.get("fuser_model") or (models[0] if models else "gpt-5")
    if fuser_model not in VALID_MODELS:
        raise ValueError("invalid_parameters: fuser_model must be one of known models")

    profile_mode = p.get("profile_mode") or DEFAULT_PROFILE_MODE
    if profile_mode not in ("auto", "combined", "per_profile"):
        raise ValueError("invalid_parameters: profile_mode invalid")

    limit = int(p.get("limit", 50))
    fields = p.get("fields", "anchors_only")
    if fields not in ("anchors_only", "anchors+snippets"):
        raise ValueError("invalid_parameters: fields invalid")

    debug = bool(p.get("debug", False))

    return {
        "operation": "audit_tool",
        "tool_name": tool_name,
        "models": models,
        "fuser_model": fuser_model,
        "profile_mode": profile_mode,
        # constantes internes
        "max_bytes_per_file": MAX_BYTES_PER_FILE,
        "max_total_context_bytes": MAX_TOTAL_CONTEXT_BYTES,
        "llm_timeout_sec": LLM_TIMEOUT_SEC,
        "llm_max_concurrency": LLM_MAX_CONCURRENCY,
        "llm_max_concurrency_per_model": LLM_MAX_CONCURRENCY_PER_MODEL,
        "llm_top_n": LLM_TOP_N,
        # affichage
        "limit": limit,
        "cursor": p.get("cursor"),
        "fields": fields,
        "debug": debug,
    }
