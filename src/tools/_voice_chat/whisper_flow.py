"""Whisper transcription flow: write wav, convert to mp3, call Whisper, logs."""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional, List
import os
import json
import numpy as np
import soundfile as sf
from .utils import ensure_audio_tmp_dir
from .logs import dbg
from .utils import convert_to_mp3_16k_mono
from src.tools._media_transcribe.whisper_client import transcribe_audio_file


def write_and_transcribe(
    data: np.ndarray,
    sample_rate: int,
    whisper_model: Optional[str],
) -> Dict[str, Any]:
    tmp_dir = ensure_audio_tmp_dir()
    wav_path = tmp_dir / f"utter_{os.getpid()}_{int(os.times().elapsed*1000)}.wav"  # unique-ish
    sf.write(str(wav_path), data, samplerate=sample_rate, subtype='PCM_16')
    dbg("voice_chat_whisper_call", wav=str(wav_path.name), seconds=round(len(data)/float(sample_rate),3))
    conv = convert_to_mp3_16k_mono(wav_path)
    if not conv.get("success"):
        try:
            wav_path.unlink()
        except Exception:
            pass
        return {"error": conv.get("error", "ffmpeg conversion failed")}

    mp3_path = Path(conv["path"])  # already under chroot
    try:
        tr = transcribe_audio_file(mp3_path, whisper_model=whisper_model)
    finally:
        try:
            mp3_path.unlink()
        except Exception:
            pass
        try:
            wav_path.unlink()
        except Exception:
            pass

    dbg("voice_chat_whisper_result", success=tr.get("success"), empty=tr.get("empty"), preview=(tr.get("transcription","") or "")[:120])
    return tr
