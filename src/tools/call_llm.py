"""
call_llm tool - LLM API integration with MCP tools support (simplified params)
"""
from typing import Any, Dict, List, Optional
import os
import logging

# Import dispatcher like other tools do
from ._call_llm import core

LOG = logging.getLogger(__name__)


def _env_truthy(name: str) -> bool:
    val = os.getenv(name, "").strip().lower()
    return val in ("1", "true", "yes", "on", "debug")


if _env_truthy("LLM_DEBUG"):
    # Ensure root logger has a handler so our child loggers actually print
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [root] %(message)s")
        root.setLevel(logging.DEBUG)

    LOG.setLevel(logging.DEBUG)
    # Attach a dedicated handler to this module if missing
    if not LOG.handlers:
        h = logging.StreamHandler()
        h.setLevel(logging.DEBUG)
        h.setFormatter(logging.Formatter("%(asctime)s [call_llm] %(message)s"))
        LOG.addHandler(h)

    # Ensure submodule loggers (_call_llm.*) also output DEBUG to the same handler
    for name in (
        "tools._call_llm",
        "tools._call_llm.core",
        "tools._call_llm.streaming",
        "tools._call_llm.tool_execution",
    ):
        L2 = logging.getLogger(name)
        L2.setLevel(logging.DEBUG)
        if not L2.handlers:
            # Reuse the first handler we just created for LOG
            L2.addHandler(LOG.handlers[0])


def run(
    message: Optional[str] = None,
    promptSystem: Optional[str] = None,
    model: str = "gpt-5",
    max_tokens: Optional[int] = None,
    tool_names: Optional[List[str]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Simplified interface:
    - message: user message (string)
    - promptSystem: system instructions routed via payload.promptSystem
    Backward-compat: if `messages` is found in kwargs (array of OpenAI messages), it will be used instead of `message`.
    """
    # Build messages payload
    messages: List[Dict[str, Any]]
    if message:
        messages = [{"role": "user", "content": message}]
    else:
        # Backward-compat path
        msgs = kwargs.get("messages")
        if isinstance(msgs, list) and msgs:
            messages = msgs
        else:
            return {"error": "message required"}

    extra = {}
    if promptSystem:
        extra["promptSystem"] = promptSystem

    return core.execute_call_llm(messages, model, max_tokens, tool_names, **extra)


def spec() -> Dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "call_llm",
            "displayName": "LLM Orchestrator",
            "description": "Appel d'API LLM en streaming (SSE) avec option d'outillage MCP. Fournir un seul paramètre 'message' (texte utilisateur) et un 'promptSystem' optionnel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Message utilisateur (texte libre)"
                    },
                    "promptSystem": {
                        "type": "string",
                        "description": "Instructions système transmises via payload.promptSystem (et non dans messages)."
                    },
                    "model": {
                        "type": "string",
                        "description": "Modèle LLM à utiliser (default: gpt-5)"
                    },
                    "max_tokens": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 128000,
                        "description": "Nombre maximum de tokens à générer"
                    },
                    "tool_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Noms des outils MCP à rendre disponibles au LLM"
                    }
                },
                "required": ["message"],
                "additionalProperties": False
            }
        }
    }
