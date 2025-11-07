
"""VAD and TTS helpers for voice_chat (Piper preferred, fallback to macOS 'say' or pyttsx3)."""
from __future__ import annotations
from typing import Optional
import os
import re
import platform
import subprocess
import threading
import queue as q
import time
import numpy as np
import pyttsx3
import unicodedata

from .logs import dbg
from .tts_piper import PiperBackend
from .tts_piper_stream import PiperStreamBackend
from .tts_piper_cli_stream import PiperCLIStreamBackend


def pre_emphasis(block: np.ndarray, coef: float = 0.97) -> np.ndarray:
    """Simple pre-emphasis filter to reduce low-frequency noise."""
    if block.size == 0:
        return block
    # y[n] = x[n] - a * x[n-1]
    out = np.empty_like(block)
    out[0] = block[0]
    out[1:] = block[1:] - coef * block[:-1]
    return out


def rms(block: np.ndarray) -> float:
    if block.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(block), dtype=np.float64)))


def select_tts_voice(engine: pyttsx3.Engine, name: Optional[str]) -> None:
    try:
        if not name:
            return
        voices = engine.getProperty('voices') or []
        for v in voices:
            vname = getattr(v, 'name', '') or ''
            vid = getattr(v, 'id', '') or ''
            if name.lower() in vname.lower() or name.lower() in vid.lower():
                engine.setProperty('voice', v.id)
                break
    except Exception:
        pass

# --- Emoji/variants stripping + punctuation normalization for TTS ---
_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E6-\U0001F1FF"  # flags
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA70-\U0001FAFF"  # extended-A
    "\U00002600-\U000026FF"  # misc
    "\U00002700-\U000027BF"  # dingbats
    "\U0001F3FB-\U0001F3FF"  # skin tones
    "]",
    flags=re.UNICODE,
)
_VARIATION_RE = re.compile("[\u200D\uFE0E\uFE0F]")
_PUNCT_RE = re.compile(r"[\?!:;\(\)\[\]]")


def _strip_combining_marks(s: str) -> str:
    """Remove Unicode combining marks (e.g., U+0303), after NFD decomposition, then recompose to NFC."""
    if not s:
        return s
    nfd = unicodedata.normalize('NFD', s)
    stripped = ''.join(ch for ch in nfd if unicodedata.category(ch) != 'Mn')
    return unicodedata.normalize('NFC', stripped)


def sanitize_for_tts(text: str) -> str:
    """Normalize and clean text for TTS to avoid odd phonemes and over-articulation.
    - Normalize Unicode and strip combining marks (fixes 'Missing phoneme from id map: \u0303').
    - Remove emojis / variation selectors.
    - Replace ? ! : ; ( ) [ ] by commas (short pause) and collapse spaces.
    """
    if not text:
        return ""
    s = _strip_combining_marks(text)
    s = _EMOJI_RE.sub("", s)
    s = _VARIATION_RE.sub("", s)
    # Replace ? ! : ; ( ) [ ] with a comma or short pause marker (we keep commas)
    s = _PUNCT_RE.sub(",", s)
    # Collapse excessive whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


class TTSManager:
    """TTS manager: Piper CLI streaming first (robust, low latency), then Piper Python streaming,
    then Piper CLI (WAV), else macOS 'say', else pyttsx3. Runs in a background thread and is interruptible.
    """

    def __init__(self, voice: Optional[str] = None) -> None:
        self._backend = 'pyttsx3'
        self._voice = voice
        self._say_proc: Optional[subprocess.Popen] = None
        self._speaking_since: Optional[float] = None

        # Prefer CLI streaming (robust latency) first
        self._piper_cli_stream = PiperCLIStreamBackend(length_scale=0.85)
        self._piper_stream = None
        self._piper = None

        if self._piper_cli_stream.available():
            self._backend = 'piper_cli_stream'
        else:
            # Try Python streaming
            self._piper_stream = PiperStreamBackend(length_scale=0.85)
            if self._piper_stream.available():
                self._backend = 'piper_stream'
            else:
                # Fallback to Piper CLI if available
                self._piper = PiperBackend()
                if self._piper.available():
                    self._backend = 'piper'
                elif platform.system() == 'Darwin' and os.getenv('VOICE_TTS_BACKEND', '').lower() != 'pyttsx3':
                    # Prefer Apple 'say' on macOS unless overridden
                    self._backend = 'say'
                else:
                    self.engine = pyttsx3.init()
                    try:
                        select_tts_voice(self.engine, voice)
                    except Exception:
                        pass

        self._q: "q.Queue[str]" = q.Queue()
        self._stop_evt = threading.Event()
        self._thr = threading.Thread(target=self._run, name="voice_chat_tts", daemon=True)
        self._thr.start()

    def backend_name(self) -> str:
        return self._backend

    def speaking_elapsed_ms(self) -> float:
        if self._speaking_since is None:
            return 0.0
        return (time.monotonic() - self._speaking_since) * 1000.0

    # --- macOS 'say' implementation ---
    def _say_blocking(self, text: str) -> None:
        if not text:
            return
        args = ['say']
        if self._voice:
            args += ['-v', self._voice]
        try:
            self._speaking_since = time.monotonic()
            self._say_proc = subprocess.Popen(args + [text])
            self._say_proc.wait()
        except Exception:
            pass
        finally:
            self._say_proc = None
            self._speaking_since = None

    def _say_stop(self) -> None:
        try:
            if self._say_proc and self._say_proc.poll() is None:
                self._say_proc.terminate()
                try:
                    self._say_proc.wait(timeout=0.5)
                except Exception:
                    self._say_proc.kill()
        except Exception:
            pass
        finally:
            self._say_proc = None
            self._speaking_since = None

    # --- Background loop ---
    def _run(self) -> None:
        while not self._stop_evt.is_set():
            try:
                text = self._q.get(timeout=0.2)
            except q.Empty:
                continue
            if not text:
                continue
            try:
                if self._backend == 'piper_stream':
                    self._speaking_since = time.monotonic()
                    try:
                        self._piper_stream.speak_blocking(text)  # type: ignore
                    except Exception as e:
                        dbg('voice_chat_tts_fallback', from_backend='piper_stream', error=str(e))
                        # Fallback chain on same utterance
                        if hasattr(self, '_piper_cli_stream') and self._piper_cli_stream and self._piper_cli_stream.available():
                            try:
                                self._piper_cli_stream.speak_blocking(text)  # type: ignore
                                continue
                            except Exception as e2:
                                dbg('voice_chat_tts_fallback', from_backend='piper_cli_stream', error=str(e2))
                        if hasattr(self, '_piper') and self._piper and self._piper.available():
                            try:
                                self._piper.speak_blocking(text)  # type: ignore
                                continue
                            except Exception as e3:
                                dbg('voice_chat_tts_fallback', from_backend='piper', error=str(e3))
                        # Last resorts
                        if self._voice and platform.system() == 'Darwin':
                            self._say_blocking(text)
                        else:
                            if not hasattr(self, 'engine'):
                                self.engine = pyttsx3.init()
                            self.engine.say(text)  # type: ignore
                            self.engine.runAndWait()  # type: ignore
                    finally:
                        self._speaking_since = None
                elif self._backend == 'piper_cli_stream':
                    self._speaking_since = time.monotonic()
                    try:
                        self._piper_cli_stream.speak_blocking(text)  # type: ignore
                    except Exception as e2:
                        dbg('voice_chat_tts_fallback', from_backend='piper_cli_stream', error=str(e2))
                        if hasattr(self, '_piper') and self._piper and self._piper.available():
                            try:
                                self._piper.speak_blocking(text)  # type: ignore
                            except Exception:
                                self._say_or_pyttsx3(text)
                        else:
                            self._say_or_pyttsx3(text)
                    finally:
                        self._speaking_since = None
                elif self._backend == 'piper':
                    self._speaking_since = time.monotonic()
                    try:
                        self._piper.speak_blocking(text)  # type: ignore
                    except Exception:
                        self._say_or_pyttsx3(text)
                    finally:
                        self._speaking_since = None
                elif self._backend == 'say':
                    self._say_blocking(text)
                else:
                    self._speaking_since = time.monotonic()
                    if not hasattr(self, 'engine'):
                        self.engine = pyttsx3.init()
                    self.engine.say(text)  # type: ignore
                    self.engine.runAndWait()  # type: ignore
                    self._speaking_since = None
            except Exception:
                self._speaking_since = None
                pass

    def _say_or_pyttsx3(self, text: str) -> None:
        if platform.system() == 'Darwin':
            self._say_blocking(text)
        else:
            if not hasattr(self, 'engine'):
                self.engine = pyttsx3.init()
            self.engine.say(text)  # type: ignore
            self.engine.runAndWait()  # type: ignore

    def speak(self, text: str) -> None:
        try:
            self._q.put_nowait(text)
        except Exception:
            pass

    def stop(self) -> None:
        """Interrupt current speech (barge-in)."""
        try:
            if self._backend == 'say':
                self._say_stop()
            elif self._backend == 'piper_stream':
                self._piper_stream.stop()  # type: ignore
                self._speaking_since = None
            elif self._backend == 'piper_cli_stream':
                try:
                    self._piper_cli_stream.stop()  # type: ignore
                except Exception:
                    pass
                self._speaking_since = None
            elif self._backend == 'piper':
                # Piper CLI plays via sounddevice; stop() is enough
                try:
                    import sounddevice as sd
                    sd.stop()
                except Exception:
                    pass
                self._speaking_since = None
            else:
                if not hasattr(self, 'engine'):
                    self.engine = pyttsx3.init()
                self.engine.stop()  # type: ignore
                self._speaking_since = None
        except Exception:
            pass

    def clear_queue(self) -> None:
        try:
            while not self._q.empty():
                try:
                    self._q.get_nowait()
                except q.Empty:
                    break
        except Exception:
            pass

    def interrupt(self) -> None:
        """Stop current speech and clear any pending segments (hard barge-in)."""
        self.stop()
        self.clear_queue()

    def shutdown(self) -> None:
        self._stop_evt.set()
        try:
            self.stop()
        except Exception:
            pass
