from __future__ import annotations
from typing import Optional, Tuple
import json
import types
from pathlib import Path
import sounddevice as sd
import numpy as np

from .utils import get_project_root
from .logs import dbg


class PiperStreamBackend:
    """Best‑effort Piper backend using the Python library (piper-tts).
    - Loads the model once in memory to avoid repeated cold starts.
    - Plays immediately; supports both full-buffer and chunk/generator outputs.
    - If the Python API is unavailable or loading fails, available() returns False.
    """

    def __init__(self, length_scale: float = 0.85, noise_scale: float = 0.667, noise_w: float = 0.8) -> None:
        # Keep params for future versions that accept them; we won't pass them if unsupported
        self.length_scale = float(length_scale)
        self.noise_scale = float(noise_scale)
        self.noise_w = float(noise_w)

        self._voice = None  # type: ignore
        self._sr: int = 22050
        self._api_ok = False
        self._playing = False
        self._unavail_reason: Optional[str] = None

        try:
            from piper import PiperVoice  # type: ignore  # noqa: F401
            self._api_ok = True
        except Exception:
            self._api_ok = False
            self._unavail_reason = "piper-tts not installed"
            dbg("voice_chat_tts_stream_probe", api_ok=False, reason=self._unavail_reason)
            return

        model_path, cfg_path = self._find_model_and_config()
        dbg("voice_chat_tts_stream_model_pick", model_path=model_path, cfg_path=cfg_path)
        if not model_path or not cfg_path:
            self._unavail_reason = "model_or_config_missing"
            return
        try:
            from piper import PiperVoice  # type: ignore
            self._voice = PiperVoice.load(model_path, cfg_path)  # type: ignore
            # Read sample rate preferably from config json (audio.sample_rate)
            sr = self._read_sample_rate(cfg_path)
            if isinstance(sr, int) and sr > 4000:
                self._sr = sr
            dbg("voice_chat_tts_stream_loaded", sample_rate=self._sr, length_scale=self.length_scale)
        except Exception as e:
            self._voice = None
            self._unavail_reason = f"load_failed:{e}"
            dbg("voice_chat_tts_stream_error", error=str(e))

    def _read_sample_rate(self, cfg_path: str) -> Optional[int]:
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if isinstance(cfg, dict):
                # Prefer primary config json key
                sr = cfg.get("audio", {}).get("sample_rate") or cfg.get("sample_rate")
                if isinstance(sr, int) and sr > 4000:
                    return sr
        except Exception:
            return None
        return None

    def _find_model_and_config(self) -> Tuple[Optional[str], Optional[str]]:
        root = get_project_root() / "models" / "piper"
        if not root.is_dir():
            return None, None
        candidates = sorted(root.rglob("*.onnx"))
        if not candidates:
            return None, None

        def region_score(name: str) -> int:
            n = name.lower()
            if "fr_fr" in n or "fr-fr" in n:
                return 0
            if "fr_ca" in n or "fr-ca" in n:
                return 1
            if "fr" in n:
                return 2
            return 10

        def voice_score(name: str) -> int:
            n = name.lower()
            if "lessac" in n:
                return 0
            if "siwis" in n:
                return 1
            if "mls" in n:
                return 2
            return 5

        best = sorted(candidates, key=lambda p: (region_score(p.name), voice_score(p.name), p.name.lower()))[0]
        model_path = str(best)
        # Find config sibling
        stem = best.name[:-5] if best.name.endswith(".onnx") else best.stem
        cfg_json = best.with_name(stem + ".json")
        cfg_onnx_json = best.with_name(stem + ".onnx.json")
        if cfg_json.exists():
            return model_path, str(cfg_json)
        if cfg_onnx_json.exists():
            return model_path, str(cfg_onnx_json)
        # Fallback: search any json next to model
        for cand in best.parent.glob("*.json"):
            return model_path, str(cand)
        return model_path, None

    def available(self) -> bool:
        ok = bool(self._api_ok and self._voice is not None)
        if not ok:
            dbg("voice_chat_tts_stream_unavailable", reason=self._unavail_reason)
        return ok

    def _extract_array(self, chunk):
        """Return (arr, kind) where arr is a numpy array of samples and kind is 'i16' or 'f32'."""
        # AudioChunk object? duck-typing
        if hasattr(chunk, "samples"):
            arr = np.asarray(getattr(chunk, "samples"))
            if arr.dtype == np.int16:
                return arr, 'i16'
            return arr.astype(np.float32, copy=False), 'f32'
        if hasattr(chunk, "audio"):
            # may be bytes or ndarray
            audio = getattr(chunk, "audio")
            if isinstance(audio, (bytes, bytearray)):
                return np.frombuffer(audio, dtype=np.int16), 'i16'
            arr = np.asarray(audio)
            if arr.dtype == np.int16:
                return arr, 'i16'
            return arr.astype(np.float32, copy=False), 'f32'
        # Bare types
        if isinstance(chunk, (bytes, bytearray)):
            return np.frombuffer(chunk, dtype=np.int16), 'i16'
        arr = np.asarray(chunk)
        if arr.dtype == np.int16:
            return arr, 'i16'
        return arr.astype(np.float32, copy=False), 'f32'

    def speak_blocking(self, text: str) -> None:
        if not self.available() or not text:
            return
        total_samples = 0
        try:
            dbg("voice_chat_tts_stream_speak_start", len=len(text))
            out_audio = self._voice.synthesize(text)  # type: ignore
            # Case 1: generator/chunks → stream live
            if isinstance(out_audio, (types.GeneratorType,)) or (
                hasattr(out_audio, "__iter__") and not isinstance(out_audio, (tuple, np.ndarray, bytes, bytearray))
            ):
                dbg("voice_chat_tts_stream_mode", mode="generator", sr=self._sr)
                self._playing = True
                # Use int16 stream; convert float32 chunks on the fly
                with sd.RawOutputStream(samplerate=self._sr, channels=1, dtype='int16') as out:
                    for chunk in out_audio:  # type: ignore
                        try:
                            arr, kind = self._extract_array(chunk)
                            if kind == 'i16':
                                out.write(arr.tobytes())
                                total_samples += int(arr.size)
                            else:
                                np.clip(arr, -1.0, 1.0, out=arr)
                                data = (arr * 32767.0).astype(np.int16)
                                out.write(data.tobytes())
                                total_samples += int(data.size)
                        except Exception as e:
                            dbg("voice_chat_tts_stream_chunk_error", error=str(e))
                            continue
                dbg("voice_chat_tts_stream_stats", chunks="unknown", est_samples=total_samples)
                if total_samples <= 0:
                    raise RuntimeError("piper_stream_empty_audio")
                return
            # Case 2: full buffer (tuple or array or bytes)
            if isinstance(out_audio, tuple) and len(out_audio) >= 1:
                audio = out_audio[0]
                sr = int(out_audio[1]) if len(out_audio) > 1 else self._sr
            else:
                audio = out_audio
                sr = self._sr
            if isinstance(audio, (bytes, bytearray)):
                arr = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                arr = np.asarray(audio, dtype=np.float32)
            if arr.size == 0:
                dbg("voice_chat_tts_stream_empty_audio")
                raise RuntimeError("piper_stream_empty_audio")
            self._playing = True
            est_ms = int(1000.0 * arr.shape[0] / float(sr))
            dbg("voice_chat_tts_stream_play", samples=arr.shape[0], sr=sr, est_ms=est_ms)
            sd.play(arr, sr, blocking=True)
        except Exception as e:
            dbg("voice_chat_tts_stream_exception", error=str(e))
            raise
        finally:
            try:
                sd.stop()
            except Exception:
                pass
            self._playing = False
            dbg("voice_chat_tts_stream_end")

    def stop(self) -> None:
        try:
            if self._playing:
                sd.stop()
        except Exception:
            pass
        finally:
            self._playing = False
