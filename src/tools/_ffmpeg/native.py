from __future__ import annotations
import time
from typing import List, Tuple, Dict, Any, Optional

try:
    import av  # type: ignore
    import numpy as np  # type: ignore
    _HAS_PYAV = True
except Exception:
    _HAS_PYAV = False

from .utils import percentile, moving_average, hysteresis_segments, nms_time


def frames_luma_diffs(path_abs: str, scale_w: int = 64, scale_h: int = 64) -> Tuple[List[float], List[float], float]:
    """Decode at native fps with PyAV, compute luma L1 diffs between consecutive frames.
    Returns (times[], diffs[], fps_est).
    """
    if not _HAS_PYAV:
        return [], [], 0.0
    times: List[float] = []
    diffs: List[float] = []
    prev_arr: Optional['np.ndarray'] = None
    fps_est = 0.0
    try:
        with av.open(path_abs) as container:
            stream = container.streams.video[0]
            if getattr(stream, 'average_rate', None):
                try:
                    fps_est = float(stream.average_rate)
                except Exception:
                    fps_est = 0.0
            for packet in container.demux(stream):
                for frame in packet.decode():
                    fr = frame.reformat(width=scale_w, height=scale_h, format='gray')
                    arr = fr.to_ndarray()
                    # time
                    t = None
                    try:
                        if frame.pts is not None and stream.time_base is not None:
                            t = float(frame.pts * stream.time_base)
                    except Exception:
                        t = None
                    if t is None:
                        try:
                            t = float(frame.time)
                        except Exception:
                            t = None
                    if t is None:
                        t = float(len(times)) / max(1.0, fps_est or 25.0)
                    if prev_arr is not None:
                        d = float(np.abs(arr.astype(np.int16) - prev_arr.astype(np.int16)).sum()) / float(scale_w * scale_h * 255.0)
                        diffs.append(d)
                        times.append(round(t, 6))
                    prev_arr = arr
    except Exception:
        return [], [], 0.0
    if not fps_est and len(times) > 1:
        total_time = times[-1] - times[0]
        if total_time > 0:
            fps_est = float(len(times)) / total_time
    return times, diffs, fps_est or 25.0


def detect_cuts_native(path_abs: str, scale_w: int = 64, scale_h: int = 64, ma_window: int = 3, threshold_floor: float = 0.0) -> Dict[str, Any]:
    t0 = time.monotonic()
    if not _HAS_PYAV:
        return {
            'cuts': [], 'diffs': [], 'r_values': [],
            'thresholds': {'low': 0, 'high': 0, 'mode': 'percentile'},
            'frames_analyzed': 0, 'avg_diff': 0, 'max_diff': 0,
            'analyzed_fps': 0.0, 'scale': [scale_w, scale_h],
            'frames_debug': [], 'avg_similarity_pct': 0.0,
            'time_sec': round(time.monotonic() - t0, 3),
            'error': 'PyAV (av) and/or NumPy not available in runtime environment'
        }

    times, diffs, fps_native = frames_luma_diffs(path_abs, scale_w, scale_h)
    if not diffs:
        return {
            'cuts': [], 'diffs': [], 'r_values': [],
            'thresholds': {'low': 0, 'high': 0, 'mode': 'percentile'},
            'frames_analyzed': 0, 'avg_diff': 0, 'max_diff': 0,
            'analyzed_fps': fps_native, 'scale': [scale_w, scale_h],
            'frames_debug': [], 'avg_similarity_pct': 0.0,
            'time_sec': round(time.monotonic() - t0, 3)
        }

    frames_analyzed = len(diffs) + 1
    avg_diff = float(sum(diffs) / max(1, len(diffs)))
    max_diff = max(diffs)

    # Smoothing (moving average)
    Rm = moving_average(diffs, k=max(1, ma_window))

    # Thresholds via percentiles
    cuts: List[Tuple[float, float]] = []
    thresholds = {'low': 0.0, 'high': 0.0, 'mode': 'percentile'}
    if Rm:
        P_low = percentile(Rm, 0.75)
        P_high = percentile(Rm, 0.95)
        T_high = max(float(threshold_floor or 0.0), P_high)
        T_low = min(P_low, T_high * 0.9)
        if T_low >= T_high:
            T_low = max(0.0, T_high * 0.8)
        thresholds = {'low': T_low, 'high': T_high, 'mode': 'percentile'}
        segs = hysteresis_segments(times, Rm, T_low, T_high)
        cuts = nms_time(segs, window_sec=0.2)

    t1 = time.monotonic()
    # Build frame-by-frame debug with similarity percentages
    frame_debug = [
        {'t': t, 'diff': float(d), 'similarity_pct': round((1.0 - float(d)) * 100.0, 3)}
        for (t, d) in zip(times, diffs)
    ]

    return {
        'cuts': cuts,
        'diffs': list(zip(times, diffs)),
        'r_values': list(zip(times, Rm if Rm else [])),
        'thresholds': thresholds,
        'frames_analyzed': frames_analyzed,
        'avg_diff': avg_diff,
        'avg_similarity_pct': round((1.0 - avg_diff) * 100.0, 3),
        'max_diff': max_diff,
        'analyzed_fps': fps_native,
        'scale': [scale_w, scale_h],
        'frames_debug': frame_debug,
        'time_sec': round(t1 - t0, 3)
    }


def refine_cuts_native(path_abs: str, cuts_with_strength: List[Tuple[float, float]], duration: float, window_sec: float = 0.5, scale: int = 48) -> List[Dict[str, Any]]:
    """Refine cut times nativement (PyAV): pour chaque cut coarse t_c, scanne [t_c-window, t_c+window]
    à fps natif et sélectionne la frame de diff max. Retourne la liste triée par temps.
    """
    refined: List[Dict[str, Any]] = []
    if not _HAS_PYAV or not cuts_with_strength:
        return refined
    for (tc, strength) in cuts_with_strength:
        start = max(0.0, tc - window_sec)
        end = min(duration, tc + window_sec)
        if end <= start:
            continue
        local: List[Tuple[float, float]] = []
        best_d = -1.0
        best_t = tc
        try:
            with av.open(path_abs) as container:
                stream = container.streams.video[0]
                prev_arr: Optional['np.ndarray'] = None
                for packet in container.demux(stream):
                    for frame in packet.decode():
                        # Compute time for frame
                        t = None
                        try:
                            if frame.pts is not None and stream.time_base is not None:
                                t = float(frame.pts * stream.time_base)
                        except Exception:
                            t = None
                        if t is None:
                            try:
                                t = float(frame.time)
                            except Exception:
                                t = None
                        if t is None:
                            continue
                        if t < start:
                            continue
                        if t > end:
                            break
                        # Process grayscale scaled frame
                        fr = frame.reformat(width=scale, height=scale, format='gray')
                        arr = fr.to_ndarray()
                        if prev_arr is not None:
                            d = float(np.abs(arr.astype(np.int16) - prev_arr.astype(np.int16)).sum()) / float(scale * scale * 255.0)
                            local.append((round(t, 6), float(d)))
                            if d > best_d:
                                best_d = d
                                best_t = t
                        else:
                            # seed
                            local.append((round(t, 6), 0.0))
                        prev_arr = arr
        except Exception:
            pass
        refined.append({'time': round(best_t, 6), 'best_diff': float(best_d if best_d >= 0 else strength), 'window_start': start, 'fps': None, 'local_diffs': local})
    refined.sort(key=lambda x: x['time'])
    return refined
