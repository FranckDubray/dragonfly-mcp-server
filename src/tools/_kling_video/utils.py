import os
import base64
import shutil
import subprocess
import requests
from typing import Optional

PROJECT_ROOT = os.path.abspath(os.getcwd())
DOCS_VIDEO_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, 'docs', 'video'))
DOCS_IMAGES_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, 'docs', 'images'))

SESSION = requests.Session()


def ensure_dirs() -> None:
    os.makedirs(DOCS_VIDEO_DIR, exist_ok=True)
    os.makedirs(DOCS_IMAGES_DIR, exist_ok=True)


def resolve_under(base_dir: str, path: str) -> str:
    base_dir = os.path.abspath(base_dir)
    if not os.path.isabs(path):
        path = os.path.join(base_dir, path)
    abs_path = os.path.abspath(path)
    if not abs_path.startswith(base_dir + os.sep) and abs_path != base_dir:
        raise ValueError(f"Path must be under {base_dir}")
    return abs_path


def is_url(s: str) -> bool:
    return s.startswith('http://') or s.startswith('https://')


def file_to_base64_no_prefix(path: str) -> str:
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def safe_filename(name: str, ext: str) -> str:
    name = ''.join(c for c in name if c.isalnum() or c in ('-', '_')) or 'video'
    if not name.lower().endswith(ext):
        name += ext
    return name


def download_to(path: str, url: str) -> None:
    with SESSION.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in r.iter_content(8192):
                if chunk:
                    f.write(chunk)


def ffmpeg_thumbnail(src_video: str, out_webp: str) -> None:
    if shutil.which('ffmpeg') is None:
        return
    # Grab a representative frame around 0.5s, scale down keeping aspect
    cmd = [
        'ffmpeg', '-y', '-ss', '0.5', '-i', src_video,
        '-frames:v', '1', '-vf', 'thumbnail,scale=640:-1', out_webp
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
