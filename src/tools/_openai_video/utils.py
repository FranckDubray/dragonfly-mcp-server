import os
import shutil
import subprocess
from typing import Tuple

PROJECT_ROOT = os.path.abspath(os.getcwd())


def resolve_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    return os.path.abspath(os.path.join(PROJECT_ROOT, path))


def ensure_under_directory(path: str, base_dir: str) -> str:
    base_dir = os.path.abspath(base_dir)
    if not os.path.isabs(path):
        path = os.path.join(base_dir, path)
    abs_path = os.path.abspath(path)
    if not abs_path.startswith(base_dir + os.sep) and abs_path != base_dir:
        raise ValueError(f"Path must be under {base_dir}")
    return abs_path


def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def letterbox_with_ffmpeg(src: str, dst: str, target_w: int, target_h: int) -> None:
    """Scale image to fit target WxH without distortion, using black bars (letterbox/pillarbox)."""
    vf = (
        f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
        f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:color=black"
    )
    cmd = [
        "ffmpeg", "-y", "-i", src, "-vf", vf, dst
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def parse_size(size: str) -> Tuple[int, int]:
    w, h = size.split('x', 1)
    return int(w), int(h)
