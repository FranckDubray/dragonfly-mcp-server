
from __future__ import annotations
from typing import Optional, Tuple
import shutil
import subprocess
import json
import sys
from pathlib import Path
import sounddevice as sd

from .utils import get_project_root


class PiperCLIStreamBackend:
    """
    Streaming via Piper CLI: synthesize to raw PCM on stdout and play through a RawOutputStream.
    - Requires `piper` binary in PATH and a voice .onnx model + config (.json or .onnx.json).
    - Lowest start latency without loading the model per utterance in Python space.
    """

    def __init__(self, length_scale: float = 0.85, noise_scale: float = 0.667, noise_w: float = 0.8) -> None:
        self.length_scale = float(length_scale)
        self.noise_scale = float(noise_scale)
        self.noise_w = float(noise_w)
        self._proc: Optional[subprocess.Popen] = None
        self._sr: int = 22050
        self._model_path: Optional[str] = None
        self._cfg_path: Optional[str] = None
        self._piper_bin: Optional[str] = shutil.which("piper")
        if not self._piper_bin:
            # Also check alongside current python (venv/bin/piper)
            exe_dir = Path(sys.executable).resolve().parent
            cand = exe_dir / ("piper.exe" if sys.platform.startswith("win") else "piper")
            if cand.exists() and cand.is_file():
                self._piper_bin = str(cand)

        if not self._piper_bin:
            return
        self._model_path, self._cfg_path = self._find_model_and_config()
        if not self._model_path or not self._cfg_path:
            return
        sr = self._read_sample_rate(self._cfg_path)
        if isinstance(sr, int) and sr > 4000:
            self._sr = sr

    def available(self) -> bool:
        return bool(self._piper_bin and self._model_path)

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
        # Any json nearby
        for cand in best.parent.glob("*.json"):
            return model_path, str(cand)
        return model_path, None

    def _read_sample_rate(self, cfg_path: str) -> Optional[int]:
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if isinstance(cfg, dict):
                sr = cfg.get("audio", {}).get("sample_rate") or cfg.get("sample_rate")
                if isinstance(sr, int):
                    return sr
        except Exception:
            return None
        return None

    def speak_blocking(self, text: str) -> None:
        if not self.available() or not text:
            return
        # Start Piper process that writes raw 16-bit PCM to stdout
        args = [
            self._piper_bin,
            "--model", self._model_path,
            "--output_raw",
            "--length_scale", str(self.length_scale),
            "--noise_scale", str(self.noise_scale),
            "--noise_w", str(self.noise_w),
        ]
        try:
            self._proc = subprocess.Popen(
                args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            self._proc = None
            return
        try:
            assert self._proc and self._proc.stdin and self._proc.stdout
            # Feed text
            self._proc.stdin.write(text.encode("utf-8"))
            self._proc.stdin.close()
            # Stream stdout to audio device
            with sd.RawOutputStream(samplerate=self._sr, channels=1, dtype='int16') as out:
                while True:
                    chunk = self._proc.stdout.read(2048)  # smaller chunk for lower latency
                    if not chunk:
                        break
                    out.write(chunk)
            self._proc.wait(timeout=5)
        except Exception:
            try:
                if self._proc:
                    self._proc.kill()
            except Exception:
                pass
        finally:
            self._proc = None

    def stop(self) -> None:
        try:
            if self._proc and (self._proc.poll() is None):
                self._proc.kill()
        except Exception:
            pass
        finally:
            self._proc = None
