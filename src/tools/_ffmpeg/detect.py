from __future__ import annotations
from typing import Dict, Any, List, Tuple
import time, subprocess

# Prefer native decoding via PyAV when available
from .native import detect_cuts_native, frames_luma_diffs
from .utils import percentile, median_window, moving_average, read_exact, hysteresis_segments, nms_time
from .shell import run

# --------------------
# Probes
# --------------------

def probe_duration(path_abs: str) -> float:
    # Try ffprobe (simple and robust)
    code, out, err = run(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{path_abs}"')
    if code != 0:
        return 0.0
    try:
        return float(out.strip())
    except Exception:
        return 0.0


def get_avg_fps(path_abs: str) -> float:
    for entry in ("avg_frame_rate", "r_frame_rate"):
        code, out, err = run(f'ffprobe -v error -select_streams v:0 -show_entries stream={entry} -of default=noprint_wrappers=1:nokey=1 "{path_abs}"')
        if code == 0:
            s = out.strip()
            try:
                if "/" in s:
                    a, b = s.split("/")
                    a, b = float(a), float(b)
                    if b != 0:
                        return a / b
                else:
                    return float(s)
            except Exception:
                pass
    return 25.0

# --------------------
# Public API
# --------------------

def detect_cuts_similarity_info_native(path_abs: str, scale_w: int = 64, scale_h: int = 64, ma_window: int = 3, threshold_floor: float = 0.0) -> Dict[str, Any]:
    return detect_cuts_native(path_abs, scale_w=scale_w, scale_h=scale_h, ma_window=ma_window, threshold_floor=threshold_floor)


def detect_cuts_similarity_info(path_abs: str, analyze_fps: float, scale_w: int, scale_h: int, threshold_floor: float) -> Dict[str, Any]:
    """
    Legacy coarse detection via ffmpeg CLI (downsampled). Native pass is preferred.
    (Kept for compatibility; not used when PyAV native is available.)
    """
    t0 = time.monotonic()
    if analyze_fps <= 0:
        analyze_fps = 24.0
    cmd = [
        'ffmpeg', '-hide_banner', '-loglevel', 'error',
        '-i', path_abs,
        '-vf', f'fps={analyze_fps},scale={scale_w}:{scale_h},format=gray',
        '-f', 'rawvideo', '-'
    ]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    frame_size = scale_w * scale_h
    prev = None
    idx = 0
    times: List[float] = []
    diffs: List[float] = []
    sum_diff = 0.0
    max_diff = 0.0
    def _read_exact(pipe, n: int) -> bytes:
        buf = bytearray()
        need = n
        while need > 0:
            chunk = pipe.read(need)
            if not chunk:
                break
            buf += chunk
            need -= len(chunk)
        return bytes(buf)
    while True:
        buf = _read_exact(p.stdout, frame_size) if p.stdout else b''
        if len(buf) < frame_size:
            break
        if prev is not None:
            total = 0
            for i in range(frame_size):
                total += abs(buf[i] - prev[i])
            diff = total / float(frame_size * 255.0)
            t = idx / analyze_fps
            times.append(round(t, 6))
            diffs.append(float(diff))
            sum_diff += diff
            if diff > max_diff:
                max_diff = diff
        prev = buf
        idx += 1
    try:
        p.terminate()
    except Exception:
        pass

    frames_analyzed = idx
    avg_diff = (sum_diff / max(1, len(diffs))) if diffs else 0.0

    # Smooth with EMA fast/slow + residual + median
    F: List[float] = []
    S: List[float] = []
    alpha_f = 0.6
    alpha_s = 0.05
    for i, d in enumerate(diffs):
        if i == 0:
            F.append(d)
            S.append(d)
        else:
            F.append((1 - alpha_f) * F[-1] + alpha_f * d)
            S.append((1 - alpha_s) * S[-1] + alpha_s * d)
    R = [max(0.0, f - s) for f, s in zip(F, S)]
    # median on R
    from .utils import median_window as _median_window
    Rm = _median_window(R, k=3)

    # thresholds
    from .utils import percentile as _percentile
    cuts: List[Tuple[float, float]] = []
    thresholds = {'low': 0.0, 'high': 0.0, 'mode': 'percentile'}
    if Rm:
        P_low = _percentile(Rm, 0.75)
        P_high = _percentile(Rm, 0.95)
        T_high = max(float(threshold_floor or 0.0), P_high)
        T_low = min(P_low, T_high * 0.9)
        if T_low >= T_high:
            T_low = max(0.0, T_high * 0.8)
        thresholds = {'low': T_low, 'high': T_high, 'mode': 'percentile'}

        from .utils import hysteresis_segments as _hyst, nms_time as _nms
        segs = _hyst(times, Rm, T_low, T_high)
        cuts = _nms(segs, window_sec=0.2)

    cap = 2000
    diffs_out = list(zip(times[:cap], diffs[:cap]))
    r_out = list(zip(times[:cap], Rm[:cap] if Rm else []))

    t1 = time.monotonic()
    return {
        'cuts': cuts,
        'diffs': diffs_out,
        'r_values': r_out,
        'thresholds': thresholds,
        'frames_analyzed': frames_analyzed,
        'avg_diff': avg_diff,
        'max_diff': max_diff,
        'analyzed_fps': analyze_fps,
        'scale': [scale_w, scale_h],
        'time_sec': round(t1 - t0, 3)
    }
