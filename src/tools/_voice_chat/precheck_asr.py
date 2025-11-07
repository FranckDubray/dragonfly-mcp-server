from __future__ import annotations
from typing import Dict, Any, Optional
import os
import re
import numpy as np
from pathlib import Path

# Optional lightweight pre-ASR with Vosk to gate short utterances (yes/no/wait...).
try:
    from vosk import Model, KaldiRecognizer  # type: ignore
except Exception:  # pragma: no cover
    Model = None  # type: ignore
    KaldiRecognizer = None  # type: ignore

# Prefer robust project-root resolution to avoid CWD issues
try:
    from .utils import get_project_root  # type: ignore
except Exception:  # fallback if utils import fails
    def get_project_root() -> Path:
        cur = Path(__file__).resolve()
        while cur != cur.parent:
            if (cur / 'pyproject.toml').exists() or (cur / '.git').exists():
                return cur
            cur = cur.parent
        return Path.cwd()

_MODEL: Optional[Model] = None  # type: ignore

# Common short intents (French): affirmative, negative, wait/pause, go/continue
_SHORT_LEXICON = [
    r"\boui\b", r"\bouais\b", r"\bok\b", r"\bd'accord\b",
    r"\bvas[ -]?y\b", r"\bcontinue\b",
    r"\bnon\b", r"\bpas du tout\b",
    r"\battends?\b", r"\bune? minute\b", r"\bpause\b", r"\bstop(pe)?\b",
]
_SHORT_RE = re.compile("|".join(_SHORT_LEXICON), flags=re.IGNORECASE)


def _find_vosk_model_dir() -> Optional[str]:
    """Best-effort lookup for a local Vosk FR model (absolute paths from project root).
    Expected locations (any of):
    - models/vosk/vosk-model-small-fr-0.22
    - models/vosk/fr-small
    - models/vosk/fr
    Returns the first that exists, else None.
    """
    root = get_project_root()
    candidates = [
        root / "models" / "vosk" / "vosk-model-small-fr-0.22",
        root / "models" / "vosk" / "fr-small",
        root / "models" / "vosk" / "fr",
    ]
    for p in candidates:
        if p.is_dir():
            return str(p)
    return None


def _ensure_model() -> Optional[Model]:  # type: ignore
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    if Model is None:
        return None
    mdir = _find_vosk_model_dir()
    if not mdir:
        return None
    try:
        _MODEL = Model(mdir)  # type: ignore
        return _MODEL
    except Exception:
        return None


def _f32_to_i16_bytes(data: np.ndarray) -> bytes:
    if data.dtype != np.float32:
        data = data.astype(np.float32, copy=False)
    np.clip(data, -1.0, 1.0, out=data)
    return (data * 32767.0).astype(np.int16).tobytes()


def precheck_short(data_f32: np.ndarray, sample_rate: int) -> Dict[str, Any]:
    """Attempt a fast, local recognition for very short utterances.
    Returns {"hit": bool, "text": str, "avg_conf": float, "reason": str}.
    hit=True means we can skip Whisper and use returned text.
    """
    if sample_rate != 16000 or data_f32.size == 0:
        return {"hit": False, "reason": "bad_input", "text": "", "avg_conf": 0.0}

    # Differentiate missing package vs missing model on disk
    if Model is None:
        return {"hit": False, "reason": "vosk_not_installed", "text": "", "avg_conf": 0.0}

    model = _ensure_model()
    if model is None:
        return {"hit": False, "reason": "vosk_model_missing", "text": "", "avg_conf": 0.0}

    try:
        pcm = _f32_to_i16_bytes(data_f32)
        rec = KaldiRecognizer(model, 16000)  # type: ignore
        rec.SetWords(True)
        ok = rec.AcceptWaveform(pcm)
        if ok:
            import json
            result = json.loads(rec.Result())
        else:
            import json
            result = json.loads(rec.FinalResult())
        text = (result.get("text") or "").strip()
        words = result.get("result") or []
        confs = [float(w.get("conf", 0.0)) for w in words if isinstance(w, dict)]
        avg_conf = (sum(confs) / len(confs)) if confs else 0.0
        # Lexicon match for short commands
        if text and _SHORT_RE.search(text) and avg_conf >= 0.5:
            return {"hit": True, "text": text, "avg_conf": avg_conf, "reason": "lexicon_match"}
        return {"hit": False, "text": text, "avg_conf": avg_conf, "reason": "no_match"}
    except Exception as e:
        return {"hit": False, "reason": f"vosk_error:{e}", "text": "", "avg_conf": 0.0}
