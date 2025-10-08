from __future__ import annotations
import time
import subprocess
from typing import List, Tuple, Dict, Any
from .shell import run

# --------------------
# Probes
# --------------------

def probe_duration(path_abs: str) -> float:
    code, out, err = run(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{path_abs}"')
    if code != 0:
        return 0.0
    try:
        return float(out.strip())
    except Exception:
        return 0.0


def get_avg_fps(path_abs: str) -> float:
    # Try avg_frame_rate then r_frame_rate
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
# Utilities
# --------------------

def _percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    v = sorted(values)
    idx = max(0, min(len(v) - 1, int(p * (len(v) - 1))))
    return v[idx]


def _median_window(vals: List[float], k: int = 3) -> List[float]:
    if not vals:
        return []
    n = len(vals)
    if k <= 1 or k > n:
        return vals[:]
    half = k // 2
    out: List[float] = []
    for i in range(n):
        a = max(0, i - half)
        b = min(n, i + half + 1)
        window = sorted(vals[a:b])
        m = window[len(window)//2]
        out.append(m)
    return out


def _read_exact(pipe, n: int) -> bytes:
    """Read exactly n bytes from pipe or return fewer if EOF."""
    buf = bytearray()
    need = n
    while need > 0:
        chunk = pipe.read(need)
        if not chunk:
            break
        buf += chunk
        need -= len(chunk)
    return bytes(buf)

# --------------------
# Coarse detection (palier 5: luma + smoothing + hysteresis)
# --------------------

def detect_cuts_similarity_info(path_abs: str, analyze_fps: float, scale_w: int, scale_h: int, threshold_floor: float) -> Dict[str, Any]:
    """
    Coarse pass haute sensibilité (luma):
    - fps analyse (def 24), scale (def 48x48), format=gray
    - Diff L1 frame->frame (luma)
    - Lissage EMA rapide/lente + médiane (k=3)
    - Hystérésis: T_low=max(0.08,P40), T_high=max(0.18,P70)
    - NMS 0.05s
    Retourne: cuts, diffs (t,d), r_values (t,R), thresholds, stats
    """
    t0 = time.monotonic()
    if analyze_fps <= 0:
        analyze_fps = 24.0
    # Build ffmpeg command streaming raw luma frames
    cmd = [
        'ffmpeg', '-hide_banner', '-loglevel', 'error',
        '-i', path_abs,
        '-vf', f'fps={analyze_fps},scale={scale_w}:{scale_h},format=gray',
        '-f', 'rawvideo', '-'
    ]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    frame_size = scale_w * scale_h  # 1 byte per pixel (Y)
    prev = None
    idx = 0
    times: List[float] = []
    diffs: List[float] = []
    sum_diff = 0.0
    max_diff = 0.0
    while True:
        buf = _read_exact(p.stdout, frame_size) if p.stdout else b''
        if len(buf) < frame_size:
            break
        if prev is not None:
            total = 0
            # L1 on luma
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
    Rm = _median_window(R, k=3)

    # Hysteresis thresholds on Rm
    cuts: List[Tuple[float, float]] = []
    thresholds = {'low': 0.08, 'high': 0.18}
    if Rm:
        T_low = max(0.08, _percentile(Rm, 0.40))
        T_high = max(0.18, _percentile(Rm, 0.70))
        thresholds = {'low': T_low, 'high': T_high}
        # candidates above high
        cand: List[Tuple[float, float]] = []
        for t, r in zip(times, Rm):
            if r > T_high:
                cand.append((t, r))
        # NMS 0.05s
        cand.sort(key=lambda x: x[0])
        nms: List[Tuple[float, float]] = []
        last_t = -1e9
        for (t, r) in cand:
            if nms and (t - last_t) < 0.05:
                if r > nms[-1][1]:
                    nms[-1] = (t, r)
                    last_t = t
                continue
            nms.append((t, r))
            last_t = t
        cuts = nms

    # Cap for debug size
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

# --------------------
# Native FPS refinement (read-exact)
# --------------------

def refine_cuts_native(path_abs: str, cuts_with_strength: List[Tuple[float, float]], fps_native: float, duration: float, window_sec: float = 0.33) -> List[Dict[str, Any]]:
    refined: List[Dict[str, Any]] = []
    if not cuts_with_strength:
        return refined
    for (tc, strength) in cuts_with_strength:
        start = max(0.0, tc - window_sec)
        end = min(duration, tc + window_sec)
        dur = max(0.0, end - start)
        if dur <= 0.0:
            continue
        cmd = [
            'ffmpeg', '-hide_banner', '-loglevel', 'error',
            '-ss', f'{start}', '-t', f'{dur}', '-i', path_abs,
            '-vf', f'fps={fps_native},scale=48:48,format=gray',
            '-f', 'rawvideo', '-'
        ]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        frame_size = 48 * 48
        prev = None
        idx = 0
        best_d = -1.0
        best_i = -1
        local: List[Tuple[float, float]] = []
        while True:
            buf = _read_exact(p.stdout, frame_size) if p.stdout else b''
            if len(buf) < frame_size:
                break
            if prev is not None:
                total = 0
                for i in range(frame_size):
                    total += abs(buf[i] - prev[i])
                diff = total / float(frame_size * 255.0)
                t_local = start + (idx / max(1.0, fps_native))
                local.append((round(t_local, 6), float(diff)))
                if diff > best_d:
                    best_d = diff
                    best_i = idx
            prev = buf
            idx += 1
        try:
            p.terminate()
        except Exception:
            pass
        if best_i <= 0:
            refined.append({'time': tc, 'best_diff': strength, 'window_start': start, 'fps': fps_native, 'local_diffs': local})
        else:
            t_ref = start + (best_i / max(1.0, fps_native))
            refined.append({'time': round(t_ref, 6), 'best_diff': float(best_d), 'window_start': start, 'fps': fps_native, 'local_diffs': local})
    refined.sort(key=lambda x: x['time'])
    return refined

# (Optional) segment diffs at native fps (kept for future use)

def segment_diffs_native(path_abs: str, start: float, end: float, fps_native: float, scale: int = 32) -> List[Tuple[float, float]]:
    dur = max(0.0, end - start)
    if dur <= 0.0:
        return []
    cmd = [
        'ffmpeg', '-hide_banner', '-loglevel', 'error',
        '-ss', f'{start}', '-t', f'{dur}', '-i', path_abs,
        '-vf', f'fps={fps_native},scale={scale}:{scale},format=gray',
        '-f', 'rawvideo', '-'
    ]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    frame_size = scale * scale
    prev = None
    idx = 0
    out: List[Tuple[float, float]] = []
    while True:
        buf = _read_exact(p.stdout, frame_size) if p.stdout else b''
        if len(buf) < frame_size:
            break
        if prev is not None:
            total = 0
            for i in range(frame_size):
                total += abs(buf[i] - prev[i])
            diff = total / float(frame_size * 255.0)
            t_local = start + (idx / max(1.0, fps_native))
            out.append((round(t_local, 6), float(diff)))
        prev = buf
        idx += 1
    try:
        p.terminate()
    except Exception:
        pass
    return out
