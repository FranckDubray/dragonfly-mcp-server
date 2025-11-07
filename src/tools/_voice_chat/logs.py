"""Logging + VAD stats helpers for voice_chat (controlled by VOICE_CHAT_DEBUG).
- dbg(event, **fields)
- VADStats: accumulate per-block metrics, emit a single recap between LLM calls
"""
from __future__ import annotations
import os, json, time
from typing import Any, Dict, Optional


def dbg(event: str, **fields: Any) -> None:
    mode = os.getenv("VOICE_CHAT_DEBUG", "0").lower()
    if mode in ("0", "false", "no", ""):
        return
    try:
        payload = {"event": event}
        payload.update(fields)
        print(json.dumps(payload, ensure_ascii=False))
    except Exception:
        pass


class VADStats:
    """Accumulate VAD metrics between two calls (Whisper/LLM) and emit a recap once."""
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        now = time.monotonic()
        self.start_ts = now
        self.samples = 0
        self.level_db_min: Optional[float] = None
        self.level_db_max: Optional[float] = None
        self.level_db_sum = 0.0
        self.snr_db_min: Optional[float] = None
        self.snr_db_max: Optional[float] = None
        self.snr_db_sum = 0.0
        self.voiced_ms = 0.0
        self.silence_ms = 0.0
        self.peaks = 0
        self.starts = 0
        self.barge = 0
        self.relief = 0
        self.grace_suppressed = 0
        self.thr_start = None
        self.thr_stop = None

    def add_sample(self, *, level_db: float, snr_db: float, thr: float, voiced: bool, block_ms: float, within_grace: bool) -> None:
        self.samples += 1
        self.level_db_sum += level_db
        self.snr_db_sum += snr_db
        if self.level_db_min is None or level_db < self.level_db_min:
            self.level_db_min = level_db
        if self.level_db_max is None or level_db > self.level_db_max:
            self.level_db_max = level_db
        if self.snr_db_min is None or snr_db < self.snr_db_min:
            self.snr_db_min = snr_db
        if self.snr_db_max is None or snr_db > self.snr_db_max:
            self.snr_db_max = snr_db
        if voiced and not within_grace:
            self.voiced_ms += block_ms
        else:
            self.silence_ms += block_ms

    def add_event(self, name: str, **extra: Any) -> None:
        if name == "peak":
            self.peaks += 1
        elif name == "start":
            self.starts += 1
        elif name == "barge":
            self.barge += 1
        elif name == "relief":
            self.relief += 1
        elif name == "grace_suppressed":
            self.grace_suppressed += 1
        # thresholds can be recorded via extra
        ts = extra.get("thr_start")
        te = extra.get("thr_stop")
        if ts is not None:
            self.thr_start = ts
        if te is not None:
            self.thr_stop = te

    def recap_and_reset(self) -> Dict[str, Any]:
        dur_ms = (time.monotonic() - self.start_ts) * 1000.0
        avg_level = (self.level_db_sum / self.samples) if self.samples else 0.0
        avg_snr = (self.snr_db_sum / self.samples) if self.samples else 0.0
        out = {
            "event": "voice_chat_vad_recap",
            "duration_ms": round(dur_ms, 1),
            "samples": self.samples,
            "level_db_min": None if self.level_db_min is None else round(self.level_db_min, 2),
            "level_db_avg": round(avg_level, 2),
            "level_db_max": None if self.level_db_max is None else round(self.level_db_max, 2),
            "snr_db_min": None if self.snr_db_min is None else round(self.snr_db_min, 2),
            "snr_db_avg": round(avg_snr, 2),
            "snr_db_max": None if self.snr_db_max is None else round(self.snr_db_max, 2),
            "voiced_ms": round(self.voiced_ms, 1),
            "silence_ms": round(self.silence_ms, 1),
            "peaks": self.peaks,
            "starts": self.starts,
            "barge": self.barge,
            "relief": self.relief,
            "grace_suppressed": self.grace_suppressed,
            "thr_start": self.thr_start,
            "thr_stop": self.thr_stop,
        }
        self.reset()
        return out
