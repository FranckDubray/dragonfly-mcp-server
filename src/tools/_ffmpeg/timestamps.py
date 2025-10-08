from __future__ import annotations
from typing import List, Dict, Any, Tuple

def prune_cuts_min_scene_hardaware(cuts_with_strength: List[Tuple[float, float]], duration: float, min_scene_sec: float, hard_threshold: float) -> List[float]:
    dur = max(0.0, float(duration or 0.0))
    cuts_with_strength = [(t, s) for (t, s) in cuts_with_strength if 0.0 < t < dur]
    cuts_with_strength.sort(key=lambda x: x[0])
    kept: List[float] = []
    prev = 0.0
    for (t, strength) in cuts_with_strength:
        seg_len = t - prev
        if seg_len < min_scene_sec and strength < hard_threshold:
            continue
        kept.append(t)
        prev = t
    if kept and (dur - kept[-1]) < min_scene_sec:
        kept.pop()
    return kept


def build_shots_with_labels(scenes: List[float], duration: float, interval_unused: int, end_eps: float = 0.05) -> List[Dict[str, Any]]:
    """
    Only start and end per scene (no intraplan samples), as requested.
    """
    dur = max(0.0, float(duration or 0.0))
    cuts = [0.0]
    for t in scenes:
        if 0.0 < t < dur:
            cuts.append(t)
    if dur > 0.0:
        cuts.append(dur)
    cuts = sorted(set([round(x, 3) for x in cuts]))
    shots: List[Dict[str, Any]] = []
    for i in range(len(cuts) - 1):
        start = cuts[i]
        end_raw = cuts[i + 1]
        end = max(start, round(end_raw - end_eps, 3))
        shots.append({
            'index': i + 1,
            'start': round(start, 3),
            'end': end,
            'samples': []
        })
    return shots
