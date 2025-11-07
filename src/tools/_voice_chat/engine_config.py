from __future__ import annotations
from typing import Tuple

# Fixed constants (no environment tuning). If you need to override, use the tool JSON parameters.


def get_barge_config() -> Tuple[int, int, float, float]:
    """Return (barge_grace_ms, barge_arm_blocks, barge_snr_extra, barge_min_abs_mult)."""
    barge_grace_ms = 2000        # ms of grace before barge-in is allowed
    barge_arm_blocks = 7         # require >= ~210 ms (with 30 ms blocks) of sustained speech to barge
    barge_snr_extra = 10.0       # extra dB over base SNR gate (kept for completeness)
    barge_min_abs_mult = 4.0     # absolute minimum level relative to noise for barge
    return barge_grace_ms, barge_arm_blocks, barge_snr_extra, barge_min_abs_mult


def get_tts_max_chars() -> int:
    # Safety cap to avoid very long monologues; audio UX stays tight
    return 600


def get_snr_min_db() -> float:
    # Base SNR gate for voiced detection (outside TTS barge conditions)
    return 8.0


def get_relief_config() -> Tuple[float, float, bool]:
    """Return (interval_s, factor, to_base).
    - interval_s: how often we relax the arming threshold if nothing triggers
    - factor: multiplicative decrease of current threshold
    - to_base: allow lowering down to calibration base when needed
    """
    return 3.0, 0.85, True


def get_min_abs_mult() -> float:
    """Multiplier applied to noise_rms to gate the SNR branch of voiced detection.
    Lower values (e.g. 1.1–1.3) make detection easier for low-level mics.
    """
    return 1.2
