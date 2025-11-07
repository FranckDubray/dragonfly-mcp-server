
from __future__ import annotations
from typing import Optional
import os
import shutil
import subprocess
from pathlib import Path
import soundfile as sf
import sounddevice as sd

from .utils import ensure_audio_tmp_dir, get_project_root


class PiperBackend:
    """Lightweight Piper TTS wrapper.
    - Requires 'piper' binary in PATH (or custom install) and a .onnx voice model.
    - Generates a WAV to a temp file and plays it via sounddevice.
    """

    def __init__(self) -> None:
        self.piper_bin: Optional[str] = shutil.which("piper")
        self.model_path: Optional[str] = self._find_model()
        self._playing = False

        
    def available(self) -> bool:
        return bool(self.piper_bin and self.model_path and os.path.isfile(self.model_path))

    def _find_model(self) -> Optional[str]:
        """Search models under <project_root>/models/piper recursively and pick the best FR voice.
        Priority order:
          Region: fr_FR (0) > fr_CA (1) > fr (2) > other (10)
          Voice (within same region): lessac (0) > siwis (1) > mls (2) > others (5)
          Tiebreaker: filename
        """
        root = get_project_root() / "models" / "piper"
        candidates: list[Path] = []
        if root.is_dir():
            candidates = sorted(root.rglob("*.onnx"))
        if not candidates:
            return None

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
        return str(best)

    def speak_blocking(self, text: str) -> None:
        if not self.available() or not text:
            return
        out_dir = ensure_audio_tmp_dir()
        out_path = out_dir / "piper_tts.wav"
        try:
            # Faster speech by default: length_scale < 1 speeds up
            proc = subprocess.run(
                [
                    self.piper_bin,
                    "--model", self.model_path,
                    "--output_file", str(out_path),
                    "--length_scale", "0.85",   # faster than 0.90
                    "--noise_scale", "0.667",
                    "--noise_w", "0.8",
                ],
                input=text.encode("utf-8"),
                capture_output=True,
                timeout=30,
            )
            if proc.returncode != 0:
                return
            if not out_path.exists():
                return
            data, sr = sf.read(str(out_path), dtype='float32')
            if data.size == 0:
                return
            self._playing = True
            sd.play(data, sr, blocking=True)
        except Exception:
            pass
        finally:
            try:
                sd.stop()
            except Exception:
                pass
            self._playing = False
            try:
                if out_path.exists():
                    out_path.unlink()
            except Exception:
                pass

    def stop(self) -> None:
        try:
            if self._playing:
                sd.stop()
        except Exception:
            pass
        finally:
            self._playing = False

