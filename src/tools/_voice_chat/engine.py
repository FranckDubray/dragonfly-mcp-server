
"""Voice chat engine: orchestrator that wires stream + loop.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
import queue
import numpy as np

from .vad_tts import TTSManager
from .engine_stream import create_input_stream
from .engine_loop import run_loop


def run_voice_engine(
    *,
    messages: List[Dict[str, str]],
    tts: TTSManager,
    min_seconds: float = 0.5,
    vad_threshold: float = 0.07,
    vad_silence_ms: int = 1000,
    sample_rate: int = 16000,
    device: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 1.0,
    max_tokens: int = 50,
    whisper_model: Optional[str] = None,
    idle_timeout_s: int = 20,
    tool_names: Optional[List[str]] = None,
    system_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    q: "queue.Queue[np.ndarray]" = queue.Queue()

    # Use 30 ms blocks for tighter reactivity and alignment with WebRTC VAD frames
    stream = create_input_stream(sample_rate=sample_rate, device=device, q=q, channels=1, block_ms=30)
    try:
        stream.start()
        result = run_loop(
            q=q,
            messages=messages,
            tts=tts,
            sample_rate=sample_rate,
            min_seconds=min_seconds,
            vad_threshold=vad_threshold,
            vad_silence_ms=vad_silence_ms,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            whisper_model=whisper_model,
            idle_timeout_s=idle_timeout_s,
            tool_names=tool_names,
            system_prompt=system_prompt,
        )
        # Backward-compat safety: if idle timeout returned success=False, coerce to a graceful end
        if isinstance(result, dict) and ("idle_timeout" in result) and (result.get("success") is False):
            result = {**result, "success": True, "ended": True, "reason": "idle_timeout"}
        return result
    except Exception as e:
        return {"error": f"voice loop error: {e}"}
    finally:
        try:
            stream.stop()
        except Exception:
            pass
        try:
            stream.close()
        except Exception:
            pass
