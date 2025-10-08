from __future__ import annotations
import os
from typing import List, Dict, Any
from .shell import run
from .paths import project_root, ensure_dir


def _safe_name(base: str) -> str:
    return base.replace(' ', '_')


def extract_frames_at_times(path_abs: str, outdir_abs: str, times: List[float], image_format: str, overwrite: bool) -> List[Dict[str, Any]]:
    ensure_dir(outdir_abs)
    frames = []
    seen = set()
    for t in sorted(times):
        key = round(t, 3)
        if key in seen:
            continue
        seen.add(key)
        fname = f"frame_t{str(key).replace('.', '_')}.{image_format}"
        ofile = os.path.join(outdir_abs, fname)
        ow = "-y" if overwrite else "-n"
        cmd = f'ffmpeg -hide_banner -loglevel error -ss {key} -i "{path_abs}" -frames:v 1 {ow} "{ofile}"'
        code, out, err = run(cmd)
        if code == 0 and os.path.exists(ofile):
            rel_file = os.path.relpath(ofile, project_root())
            frames.append({"t": float(key), "file": rel_file})
    return frames


def extract_shots_labeled(path_abs: str, outdir_abs: str, shots: List[Dict[str, Any]], image_format: str, overwrite: bool) -> List[Dict[str, Any]]:
    """
    Export strictly two frames per shot: start and end.
    Filenames: scene_{index:03d}_start.{ext} and scene_{index:03d}_end.{ext}
    """
    ensure_dir(outdir_abs)
    frames: List[Dict[str, Any]] = []
    for s in shots:
        idx = s['index']
        # start
        name = _safe_name(f"scene_{idx:03d}_start")
        ofile = os.path.join(outdir_abs, f"{name}.{image_format}")
        ow = "-y" if overwrite else "-n"
        cmd = f'ffmpeg -hide_banner -loglevel error -ss {s["start"]} -i "{path_abs}" -frames:v 1 {ow} "{ofile}"'
        code, out, err = run(cmd)
        if code == 0 and os.path.exists(ofile):
            frames.append({"t": s['start'], "file": os.path.relpath(ofile, project_root()), "name": name, "kind": "start"})
        # end
        name = _safe_name(f"scene_{idx:03d}_end")
        ofile = os.path.join(outdir_abs, f"{name}.{image_format}")
        cmd = f'ffmpeg -hide_banner -loglevel error -ss {s["end"]} -i "{path_abs}" -frames:v 1 {ow} "{ofile}"'
        code, out, err = run(cmd)
        if code == 0 and os.path.exists(ofile):
            frames.append({"t": s['end'], "file": os.path.relpath(ofile, project_root()), "name": name, "kind": "end"})
    return frames


def extract_interval(path_abs: str, outdir_abs: str, interval: int, image_format: str, overwrite: bool, max_frames: int | None, duration: float) -> List[Dict[str, Any]]:
    ensure_dir(outdir_abs)
    ow = "-y" if overwrite else "-n"
    pattern = os.path.join(outdir_abs, f"frame_%06d.{image_format}")
    cmd = f'ffmpeg -hide_banner -loglevel error -i "{path_abs}" -vf "fps=1/{interval}" {ow} "{pattern}"'
    code, out, err = run(cmd)
    frames = []
    idx = 1
    while True:
        fname = pattern.replace("%06d", f"{idx:06d}")
        if not os.path.exists(fname):
            break
        t = (idx - 1) * interval
        frames.append({"t": float(t), "file": os.path.relpath(fname, project_root()), "name": f"every {interval}s {idx:06d}", "kind": "interval"})
        idx += 1
        if max_frames and len(frames) >= max_frames:
            break
    return frames
