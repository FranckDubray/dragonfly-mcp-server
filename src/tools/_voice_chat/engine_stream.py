from __future__ import annotations
from typing import Optional
import queue
import sounddevice as sd
import numpy as np


def create_input_stream(*, sample_rate: int, device: Optional[str], q: "queue.Queue[np.ndarray]", channels: int = 1, block_ms: int = 50) -> sd.InputStream:
    """Create a sounddevice InputStream that pushes float32 mono blocks into queue q."""
    blocksize = int(sample_rate * (block_ms / 1000.0))

    def _callback(indata, frames, time_info, status):  # noqa: ARG001
        try:
            q.put_nowait(indata.copy().reshape(-1))
        except Exception:
            pass

    stream = sd.InputStream(
        samplerate=sample_rate,
        channels=channels,
        dtype='float32',
        callback=_callback,
        blocksize=blocksize,
        device=device,
    )
    return stream
