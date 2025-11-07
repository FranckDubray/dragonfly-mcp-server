from __future__ import annotations
from collections import deque
from math import ceil

class Debouncer:
    """Temporal smoother for binary voiced decisions.
    - Majority vote over a sliding window (window_blocks)
    - Minimum onset duration in blocks (min_onset_blocks) to accept a new 'voiced'
    """
    def __init__(self, window_blocks: int = 5, min_onset_blocks: int = 3) -> None:
        self.window = max(1, int(window_blocks))
        self.min_onset = max(1, int(min_onset_blocks))
        self.buf = deque([False] * self.window, maxlen=self.window)
        self.onset_blocks = 0

    def reset(self) -> None:
        self.buf.clear()
        self.buf.extend([False] * self.window)
        self.onset_blocks = 0

    def update(self, raw_voiced: bool) -> bool:
        # Majority vote
        self.buf.append(bool(raw_voiced))
        votes = sum(1 for b in self.buf if b)
        stable = votes >= ceil(self.window / 2.0)
        if stable:
            self.onset_blocks += 1
        else:
            # If not stable voiced, reset onset counter
            self.onset_blocks = 0
        # Armed only if sustained for min_onset_blocks
        return stable and (self.onset_blocks >= self.min_onset)
