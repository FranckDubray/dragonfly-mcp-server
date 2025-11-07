

from __future__ import annotations
from typing import Dict, Any, List, Optional, Callable
import re
import numpy as np
from .logs import dbg
from .whisper_flow import write_and_transcribe
from .vad_tts import sanitize_for_tts
from .precheck_asr import precheck_short as precheck_vosk
from .precheck_tiny import precheck_tiny


def compute_snr_db(level: float, noise_rms: float) -> float:
    if noise_rms <= 1e-9:
        return 0.0
    import numpy as _np
    return 20.0 * float(_np.log10(max(level, 1e-9) / noise_rms))


def voiced_flag(level: float, snr_db: float, thr: float, SNR_MIN_DB: float, min_abs: float) -> bool:
    return (level >= thr) or (snr_db >= SNR_MIN_DB and level >= min_abs)


def strong_peak(level: float, snr_db: float, start_threshold: float, min_abs_barge: float, SNR_MIN_DB: float, barge_snr_extra: float) -> bool:
    return (
        (level >= max(start_threshold * 1.2, start_threshold + 0.03, min_abs_barge))
        and (snr_db >= (SNR_MIN_DB + barge_snr_extra))
    )


def _check_stop_and_maybe_end(assistant_text: str) -> Optional[Dict[str, Any]]:
    """Return an end-result dict if assistant indicates hang-up with <STOP>.
    Accept case-insensitive and surrounding whitespace, but ONLY if the whole message is exactly the tag.
    """
    s = (assistant_text or "").strip()
    if s.lower() == "<stop>":
        dbg("voice_chat_stop_tag_detected")
        return {
            "success": True,
            "ended": True,
            "reason": "stop_tag",
            "assistant_text": "<STOP>",
        }
    return None


def _strip_stop_tag_inline(text: str) -> str:
    """Remove any inline occurrences of <STOP>/<stop> to avoid TTS saying 'stop'."""
    if not text:
        return text
    return re.sub(r"(?i)<stop>", "", text).strip()


def handle_end_of_utterance(
    utter_frames: List[np.ndarray],
    last_voiced_block_idx: int,
    *,
    sample_rate: int,
    min_seconds: float,
    whisper_model: Optional[str],
    messages: List[Dict[str, str]],
    model: Optional[str],
    temperature: float,
    max_tokens: int,
    tts,
    tts_max_chars: int,
    ping_activity: Optional[Callable[[str], None]] = None,
    tool_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Finalize current utterance: trim, transcribe, LLM, TTS. Returns a dict with outcome.
    The caller is responsible for resetting recording state after this call.
    """
    # Trim to last voiced frame
    effective_frames = utter_frames[: last_voiced_block_idx + 1] if last_voiced_block_idx >= 0 else []
    data = np.concatenate(effective_frames) if effective_frames else np.array([], dtype=np.float32)

    if data.size == 0:
        dbg("voice_chat_discard_empty_after_trim")
        return {"success": False, "reason": "empty_after_trim"}

    trimmed_sec = len(data) / float(sample_rate)
    if trimmed_sec < float(min_seconds or 0.5):
        dbg("voice_chat_discard_too_short", trimmed_sec=round(trimmed_sec, 3))
        return {"success": False, "reason": "too_short"}

    # Precheck tiny (preferred on Apple Silicon) then Vosk; bypass if both unavailable
    # Tiny branch
    tiny = precheck_tiny(data, sample_rate)
    tiny_reason = (tiny.get("reason") or "").lower()
    tiny_text = (tiny.get("text") or "").strip()
    tiny_conf = float(tiny.get("conf") or 0.0)

    if tiny_reason not in ("tiny_not_available", "bad_input", "tiny_error"):
        # 3-tier with tiny
        letters = re.sub(r"[^A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF]", "", tiny_text)
        if tiny_text and len(letters) >= 3 and tiny_conf >= 0.65 and trimmed_sec <= 1.2:
            messages.append({"role": "user", "content": tiny_text})
            dbg("voice_chat_precheck_decision", mode="accept_local", engine="tiny", text=tiny_text, letters=len(letters), conf=round(tiny_conf, 3), dur_ms=int(trimmed_sec * 1000))
            from .llm_flow import call_llm
            llm = call_llm(messages, model, float(temperature or 1.0), min(int(max_tokens or 50), 30), tool_names=tool_names)
            if "error" in llm:
                messages.pop()
                dbg("voice_chat_llm_error", error=llm["error"])
                return {"success": False, "reason": "llm_error", "error": llm["error"]}
            assistant_text = (llm.get("assistant_text", "") or "").strip()
            # STOP tag?
            stop = _check_stop_and_maybe_end(assistant_text)
            if stop:
                messages.append({"role": "assistant", "content": assistant_text})
                return {**stop, "transcript": tiny_text}
            messages.append({"role": "assistant", "content": assistant_text})
            try:
                if assistant_text:
                    speakable = _strip_stop_tag_inline(assistant_text)
                    tts_text = sanitize_for_tts(speakable)
                    if tts_text:
                        truncated = False
                        if len(tts_text) > tts_max_chars:
                            tts_text = tts_text[:tts_max_chars] + "\u2026"
                            truncated = True
                        dbg("voice_chat_tts_speak", chars=len(tts_text), truncated=truncated)
                        if ping_activity:
                            try:
                                ping_activity("tts_start")
                            except Exception:
                                pass
                        tts.speak(tts_text)
            except Exception:
                pass
            return {"success": True, "transcript": tiny_text, "assistant_text": assistant_text}
        # Drop only if extremely weak
        if len(re.sub(r"[^A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF]", "", tiny_text)) < 3 and tiny_conf < 0.2 and trimmed_sec < 0.8:
            dbg("voice_chat_precheck_decision", mode="drop", engine="tiny", text_preview=tiny_text[:40], conf=round(tiny_conf, 3), dur_ms=int(trimmed_sec * 1000))
            return {"success": False, "reason": "precheck_drop"}
        # Otherwise, pass-through to Whisper below (including duration_guard)
    else:
        # Try Vosk as a secondary engine (if installed)
        vosk = precheck_vosk(data, sample_rate)
        v_reason = (vosk.get("reason") or "").lower()
        v_text = (vosk.get("text") or "").strip()
        v_conf = float(vosk.get("avg_conf") or 0.0)
        if v_reason not in ("vosk_not_installed", "vosk_model_missing", "bad_input", "vosk_error"):
            letters = re.sub(r"[^A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF]", "", v_text)
            if v_text and len(letters) >= 3 and v_conf >= 0.65 and trimmed_sec <= 1.2:
                messages.append({"role": "user", "content": v_text})
                dbg("voice_chat_precheck_decision", mode="accept_local", engine="vosk", text=v_text, letters=len(letters), conf=round(v_conf, 3), dur_ms=int(trimmed_sec * 1000))
                from .llm_flow import call_llm
                llm = call_llm(messages, model, float(temperature or 1.0), min(int(max_tokens or 50), 30), tool_names=tool_names)
                if "error" in llm:
                    messages.pop()
                    dbg("voice_chat_llm_error", error=llm["error"])
                    return {"success": False, "reason": "llm_error", "error": llm["error"]}
                assistant_text = (llm.get("assistant_text", "") or "").strip()
                # STOP tag?
                stop = _check_stop_and_maybe_end(assistant_text)
                if stop:
                    messages.append({"role": "assistant", "content": assistant_text})
                    return {**stop, "transcript": v_text}
                messages.append({"role": "assistant", "content": assistant_text})
                try:
                    if assistant_text:
                        speakable = _strip_stop_tag_inline(assistant_text)
                        tts_text = sanitize_for_tts(speakable)
                        if tts_text:
                            truncated = False
                            if len(tts_text) > tts_max_chars:
                                tts_text = tts_text[:tts_max_chars] + "\u2026"
                                truncated = True
                            dbg("voice_chat_tts_speak", chars=len(tts_text), truncated=truncated)
                            if ping_activity:
                                try:
                                    ping_activity("tts_start")
                                except Exception:
                                    pass
                            tts.speak(tts_text)
                except Exception:
                    pass
                return {"success": True, "transcript": v_text, "assistant_text": assistant_text}
            if len(letters) < 3 and v_conf < 0.2 and trimmed_sec < 0.8:
                dbg("voice_chat_precheck_decision", mode="drop", engine="vosk", text_preview=v_text[:40], conf=round(v_conf, 3), dur_ms=int(trimmed_sec * 1000))
                return {"success": False, "reason": "precheck_drop"}
        else:
            dbg("voice_chat_precheck_decision", mode="bypass", reason=v_reason, dur_ms=int(trimmed_sec * 1000))

    # Duration guard: always Whisper if >= 1.0 s
    if trimmed_sec >= 1.0:
        dbg("voice_chat_precheck_decision", mode="whisper", reason="duration_guard", conf=0.0, letters=0, dur_ms=int(trimmed_sec * 1000))
    else:
        dbg("voice_chat_precheck_decision", mode="whisper", reason="ambiguous_short", conf=0.0, letters=0, dur_ms=int(trimmed_sec * 1000))

    # Whisper path
    if ping_activity:
        try:
            ping_activity("whisper_start")
        except Exception:
            pass

    tr = write_and_transcribe(data, sample_rate, whisper_model)

    if ping_activity:
        try:
            ping_activity("whisper_done")
        except Exception:
            pass

    if not tr.get("success"):
        dbg("voice_chat_discard_whisper_error", error=tr.get("error"))
        return {"success": False, "reason": "whisper_error", "error": tr.get("error")}

    transcript = (tr.get("transcription", "") or "").strip()

    messages.append({"role": "user", "content": transcript})
    tokens_limit = min(int(max_tokens or 50), 50)
    dbg("voice_chat_new_message", role="user", content=transcript)

    if ping_activity:
        try:
            ping_activity("llm_start")
        except Exception:
            pass

    from .llm_flow import call_llm
    llm = call_llm(messages, model, float(temperature or 1.0), tokens_limit, tool_names=tool_names)

    if ping_activity:
        try:
            ping_activity("llm_done")
        except Exception:
            pass

    if "error" in llm:
        messages.pop()
        dbg("voice_chat_llm_error", error=llm["error"]) 
        return {"success": False, "reason": "llm_error", "error": llm["error"]}

    assistant_text = (llm.get("assistant_text", "") or "").strip()

    # STOP tag?
    stop = _check_stop_and_maybe_end(assistant_text)
    if stop:
        messages.append({"role": "assistant", "content": assistant_text})
        return {**stop, "transcript": transcript}

    messages.append({"role": "assistant", "content": assistant_text})

    try:
        if assistant_text:
            speakable = _strip_stop_tag_inline(assistant_text)
            tts_text = sanitize_for_tts(speakable)
            if tts_text:
                truncated = False
                if len(tts_text) > tts_max_chars:
                    tts_text = tts_text[:tts_max_chars] + "\u2026"
                    truncated = True
                dbg("voice_chat_tts_speak", chars=len(tts_text), truncated=truncated)
                if ping_activity:
                    try:
                        ping_activity("tts_start")
                    except Exception:
                        pass
                tts.speak(tts_text)
    except Exception:
        pass

    return {"success": True, "transcript": transcript, "assistant_text": assistant_text}
