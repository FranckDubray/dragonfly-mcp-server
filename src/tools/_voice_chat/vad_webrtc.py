from __future__ import annotations
from typing import Optional

# Optional dependency: webrtcvad (robust VAD from WebRTC)
try:
    import webrtcvad  # type: ignore
except Exception:  # pragma: no cover
    webrtcvad = None  # type: ignore

import numpy as np


def _float32_to_int16(data: np.ndarray) -> bytes:
    if data.dtype != np.float32:
        data = data.astype(np.float32, copy=False)
    # Clip to [-1.0, 1.0]
    np.clip(data, -1.0, 1.0, out=data)
    data_i16 = (data * 32767.0).astype(np.int16)
    return data_i16.tobytes()


class WebRTCVADWrapper:
    def __init__(self, aggressiveness: int = 2) -> None:
        self.vad = webrtcvad.Vad(aggressiveness)

    def is_speech(self, block_f32: np.ndarray, sample_rate: int) -> bool:
        """Return True if speech is detected in the given float32 mono block.
        Uses 30 ms frames; returns True if any frame is detected as speech.
        """
        if block_f32.size == 0:
            return False
        frame_ms = 30
        frame_len = int(sample_rate * (frame_ms / 1000.0))
        # Convert to 16-bit PCM mono bytes
        pcm = _float32_to_int16(block_f32)
        # Ensure we slice on exact multiples of frame_len
        bytes_per_sample = 2  # int16
        step = frame_len * bytes_per_sample
        n = len(pcm) // step
        if n == 0:
            # If block is smaller than one frame, pad to one frame
            pad_samples = frame_len - block_f32.size
            if pad_samples > 0:
                pad = np.zeros((pad_samples,), dtype=np.float32)
                pcm = _float32_to_int16(np.concatenate([block_f32, pad]))
                n = 1
        # Check frames
        for i in range(n):
            frame = pcm[i * step : (i + 1) * step]
            try:
                if self.vad.is_speech(frame, sample_rate):
                    return True
            except Exception:
                # If VAD errors on malformed frame, continue
                continue
        return False


def get_webrtc_vad(aggressiveness: int = 2) -> Optional[WebRTCVADWrapper]:
    if webrtcvad is None:
        return None
    try:
        return WebRTCVADWrapper(aggressiveness=aggressiveness)
    except Exception:
        return None
