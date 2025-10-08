from __future__ import annotations
from typing import List, Tuple


def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    v = sorted(values)
    idx = max(0, min(len(v) - 1, int(p * (len(v) - 1))))
    return v[idx]


def median_window(vals: List[float], k: int = 3) -> List[float]:
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


def moving_average(vals: List[float], k: int) -> List[float]:
    if not vals or k <= 1:
        return vals[:]
    n = len(vals)
    half = k // 2
    out: List[float] = []
    for i in range(n):
        a = max(0, i - half)
        b = min(n, i + half + 1)
        out.append(sum(vals[a:b]) / max(1, (b - a)))
    return out


def read_exact(pipe, n: int) -> bytes:
    buf = bytearray()
    need = n
    while need > 0:
        chunk = pipe.read(need)
        if not chunk:
            break
        buf += chunk
        need -= len(chunk)
    return bytes(buf)


def hysteresis_segments(times: List[float], values: List[float], T_low: float, T_high: float) -> List[Tuple[float, float]]:
    segs: List[Tuple[float, float]] = []
    in_seg = False
    seg_max_r = -1.0
    seg_max_t = -1.0
    for t, r in zip(times, values):
        if not in_seg:
            if r > T_high:
                in_seg = True
                seg_max_r = r
                seg_max_t = t
        else:
            if r > seg_max_r:
                seg_max_r = r
                seg_max_t = t
            if r <= T_low:
                segs.append((seg_max_t, seg_max_r))
                in_seg = False
                seg_max_r = -1.0
                seg_max_t = -1.0
    if in_seg and seg_max_t >= 0:
        segs.append((seg_max_t, seg_max_r))
    return segs


def nms_time(segs: List[Tuple[float, float]], window_sec: float = 0.2) -> List[Tuple[float, float]]:
    if not segs:
        return []
    segs.sort(key=lambda x: x[0])
    nms: List[Tuple[float, float]] = []
    last_t = -1e9
    for (t, r) in segs:
        if nms and (t - last_t) < window_sec:
            if r > nms[-1][1]:
                nms[-1] = (t, r)
                last_t = t
            continue
        nms.append((t, r))
        last_t = t
    return nms
