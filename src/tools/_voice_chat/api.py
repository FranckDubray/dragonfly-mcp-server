
"""API routing for voice_chat tool (single, blocking operation)."""
from __future__ import annotations
from typing import Dict, Any
from .core import run_full_voice_loop
from .logs import dbg

# Accept some common alias keys from LLMs/clients and map them to canonical names
_ALIAS_MAP = {
    "idle_timeout": "idle_timeout_s",
    "idleTimeout": "idle_timeout_s",
    "idleTimeoutS": "idle_timeout_s",
    "maxTokens": "max_tokens",
    "sampleRate": "sample_rate",
    "vadSilenceMs": "vad_silence_ms",
    "ttsVoice": "tts_voice",
}


def _normalize_params(params: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in params.items():
        canon = _ALIAS_MAP.get(k, k)
        # Do not overwrite an explicit canonical key with alias
        if canon in out and k in _ALIAS_MAP:
            continue
        out[canon] = v
    return out


def _coerce_types(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    int_keys = {"vad_silence_ms", "idle_timeout_s", "max_tokens", "sample_rate"}
    float_keys = {"min_seconds", "vad_threshold", "temperature"}
    for k in list(kwargs.keys()):
        v = kwargs[k]
        if v is None:
            continue
        if k in int_keys:
            try:
                kwargs[k] = int(v)
            except Exception:
                pass
        elif k in float_keys:
            try:
                kwargs[k] = float(v)
            except Exception:
                pass
    return kwargs


def route_operation(**params) -> Dict[str, Any]:
    """Single op tool: start the blocking voice loop until user stops or timeout.
    IMPORTANT: don't override core defaults here; only pass non-None values.
    """
    # Log raw params for diagnostics
    dbg("voice_chat_request_raw", raw=params)

    params = _normalize_params(params or {})
    allowed = (
        "min_seconds", "vad_threshold", "vad_silence_ms", "sample_rate",
        "device", "tts_voice", "model", "temperature", "max_tokens",
        "whisper_model", "idle_timeout_s", "tool_names",
    )
    kwargs: Dict[str, Any] = {}
    for k in allowed:
        if k in params and params[k] is not None:
            kwargs[k] = params[k]
    kwargs = _coerce_types(kwargs)
    dbg("voice_chat_request_params", **{k: kwargs.get(k) for k in [
        "min_seconds","vad_threshold","vad_silence_ms","sample_rate","idle_timeout_s","max_tokens","model","temperature","tts_voice"
    ]})
    return run_full_voice_loop(**kwargs)
