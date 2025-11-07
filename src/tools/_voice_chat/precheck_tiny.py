from __future__ import annotations
from typing import Dict, Any, Optional
import numpy as np

# Optional tiny pre-ASR with faster-whisper (Metal int8 on Apple Silicon)
try:
    from faster_whisper import WhisperModel  # type: ignore
except Exception:  # pragma: no cover
    WhisperModel = None  # type: ignore

_MODEL: Optional[WhisperModel] = None  # type: ignore


def _ensure_model() -> Optional["WhisperModel"]:
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    if WhisperModel is None:
        return None
    try:
        # Use tiny model with Metal + int8; falls back to CPU if Metal not available
        _MODEL = WhisperModel("tiny", device="metal", compute_type="int8")  # type: ignore
        return _MODEL
    except Exception:
        try:
            _MODEL = WhisperModel("tiny", device="cpu", compute_type="int8")  # type: ignore
            return _MODEL
        except Exception:
            return None


def precheck_tiny(data_f32: np.ndarray, sample_rate: int) -> Dict[str, Any]:
    """Fast local tiny-STT for very short utterances. Returns {hit, text, conf, reason}.
    hit=True means we can skip Whisper and use returned text.
    """
    if data_f32.size == 0 or sample_rate <= 0:
        return {"hit": False, "reason": "bad_input", "text": "", "conf": 0.0}
    try:
        model = _ensure_model()
        if model is None:
            return {"hit": False, "reason": "tiny_not_available", "text": "", "conf": 0.0}
        # faster-whisper expects float32 PCM normalized; we pass raw segment
        # Limit duration for speed; model handles the audio directly
        segments, info = model.transcribe(data_f32, language="fr", beam_size=1)
        best_text = ""
        best_conf = 0.0
        for seg in segments:
            txt = (seg.text or "").strip()
            conf = float(getattr(seg, "avg_logprob", -5.0))  # placeholder; model may expose no direct conf
            if txt:
                best_text = txt
                best_conf = conf
                break
        # Map conf (avg_logprob) to a rough 0..1 proxy if available; else keep 0 for conservative gate
        if best_conf <= -5.0:
            conf01 = 0.0
        else:
            # simple squashing: logprob ~ [-5,0] -> [0,1]
            conf01 = max(0.0, min(1.0, 1.0 + best_conf / 5.0))
        return {"hit": bool(best_text), "text": best_text, "conf": conf01, "reason": "ok"}
    except Exception as e:
        return {"hit": False, "reason": f"tiny_error:{e}", "text": "", "conf": 0.0}
