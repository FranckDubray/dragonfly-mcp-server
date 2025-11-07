
"""Core logic for voice_chat tool: glue code only.
- Fetch portal context
- Prepare TTS
- Optional intro LLM message to switch to voice mode
- Run engine loop
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
import os

from .portal import build_messages_from_portal
from .vad_tts import TTSManager, sanitize_for_tts
from .engine import run_voice_engine
from .llm_flow import call_llm
from .logs import dbg


INTRO_PROMPT_FR = (
    "À partir de maintenant, l'utilisateur t'entend en mode vocal grâce à de la synthèse vocale. "
    "Adapte‑toi immédiatement au format oral : réponses très courtes (1 à 2 phrases, ~15–25 mots max), ton naturel, chaleureux et fluide, comme une conversation humaine. "
    "N'utilise pas d'emojis, pas de listes, pas de markdown, pas de code, pas de citations, pas de parenthèses inutiles. "
    "Évite les termes techniques et les disclaimers. Ne fais aucune phrase méta (ne mentionne pas ce message ni le changement de mode). "
    "Si tu poses une question, une seule à la fois, simple et directe. Pas d'énumérations : synthétise. "
    "IMPORTANT : n'écris ni ne prononce jamais le mot <STOP> dans tes réponses normales. "
    "N'utilise <STOP> QUE si l'utilisateur te demande explicitement d'arrêter le mode vocal (ex : ‘arrête le vocal’, ‘raccroche’). "
    "Dans ce seul cas, réponds uniquement : <STOP> (sans aucun autre texte avant/après). "
    "Jusqu'ici la conversation était en mode chat ; maintenant elle est en mode vocal. "
    "Ta première réponse doit être exactement : Super, j'adore le mode vocal. Je t'écoute."
)


def run_full_voice_loop(
    min_seconds: float = 0.5,
    vad_threshold: float = 0.02,
    vad_silence_ms: int = 1000,
    sample_rate: int = 16000,
    device: Optional[str] = None,
    tts_voice: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 1.0,
    max_tokens: int = 100,
    whisper_model: Optional[str] = None,
    idle_timeout_s: int = 20,
    tool_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    user_token = os.getenv("AI_PORTAL_TOKEN")
    if not user_token:
        return {"error": "AI_PORTAL_TOKEN not set"}

    # Fixed defaults (no env tuning): tool JSON can override via params
    model = model or "openai/gpt-oss-120b"
    whisper_model = whisper_model or "whisper-large-v3"

    # 1) Build portal messages context
    ctx = build_messages_from_portal(user_token)
    if "error" in ctx:
        return ctx
    messages: List[Dict[str, str]] = list(ctx.get("messages", []))
    system_prompt: Optional[str] = ctx.get("system_prompt")

    # 2) Prepare TTS
    tts = TTSManager(voice=tts_voice)
    dbg("voice_chat_tts_backend", backend=tts.backend_name(), voice=tts_voice)

    # 3) Send intro message to LLM to switch to voice mode (no Whisper; immediate TTS)
    #    We do not change the system prompt; we add a user message and speak the assistant reply.
    try:
        intro_msg = {"role": "user", "content": INTRO_PROMPT_FR}
        messages.append(intro_msg)
        tokens_limit = min(int(max_tokens or 100), 100)
        dbg("voice_chat_intro_llm_call", model=model, max_tokens=tokens_limit)
        llm = call_llm(messages, model, float(temperature or 1.0), tokens_limit, tool_names=tool_names, system_prompt=system_prompt)
        if "success" in llm and llm.get("assistant_text") is not None:
            assistant_text = (llm.get("assistant_text", "") or "").strip()
            messages.append({"role": "assistant", "content": assistant_text})
            # Speak immediately (short message expected) — ignore a potential STOP here (shouldn't happen per prompt)
            tts_text = sanitize_for_tts(assistant_text)
            if tts_text and tts_text != "<STOP>":
                dbg("voice_chat_tts_speak", intro=True, chars=len(tts_text))
                tts.speak(tts_text)
        else:
            # If intro fails, remove it so it doesn't pollute context
            messages.pop()
    except Exception:
        # Fail silently and continue with engine
        try:
            if messages and messages[-1].get("content") == INTRO_PROMPT_FR:
                messages.pop()
        except Exception:
            pass

    # 4) Run engine loop
    result = run_voice_engine(
        messages=messages,
        tts=tts,
        min_seconds=min_seconds,
        vad_threshold=vad_threshold,
        vad_silence_ms=vad_silence_ms,
        sample_rate=sample_rate,
        device=device,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        whisper_model=whisper_model,
        idle_timeout_s=idle_timeout_s,
        tool_names=tool_names,
        system_prompt=system_prompt,
    )

    # Ensure TTS process is shutdown
    try:
        tts.shutdown()
    except Exception:
        pass

    return result
