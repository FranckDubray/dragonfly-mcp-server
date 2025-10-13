import os
from typing import Dict, Iterator, List, Tuple

DEFAULT_EXCLUDE_DIRS = {
    ".git", "node_modules", "vendor", "dist", "build", ".venv", ".mypy_cache",
    ".pytest_cache", ".cache", "target", "coverage", "__pycache__", "snapshots"
}
DEFAULT_EXCLUDE_FILES_PREFIX = {"README", "CHANGELOG", "LICENSE", "CONTRIBUTING", "CODE_OF_CONDUCT", "SECURITY"}
DEFAULT_EXCLUDE_GLOBS = {".min.js", ".min.css"}
BINARY_EXTS = {
    "png","jpg","jpeg","gif","webp","ico","pdf","zip","tar","gz","7z","rar",
    "mp3","mp4","mov","avi","mkv","exe","dll","so","dylib","bin"
}

READ_BYTES_PER_FILE = 64 * 1024  # 64KB head cap for content reads


def is_binary_filename(name: str) -> bool:
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return ext in BINARY_EXTS


def iter_files(root: str, scope_path: str | None = None,
               max_files_scanned: int = 10000) -> Iterator[Tuple[str, int]]:
    base = os.path.abspath(root)
    start = os.path.join(base, scope_path) if scope_path else base
    scanned = 0
    for dirpath, dirnames, filenames in os.walk(start):
        # Exclude directories
        dirnames[:] = [d for d in dirnames if d not in DEFAULT_EXCLUDE_DIRS and not d.startswith(".")]
        for fn in filenames:
            if scanned >= max_files_scanned:
                return
            # Exclude common large docs by prefix
            basefn = os.path.basename(fn)
            if any(basefn.upper().startswith(pref) for pref in DEFAULT_EXCLUDE_FILES_PREFIX):
                continue
            # Skip binary by extension
            if is_binary_filename(fn):
                continue
            full = os.path.join(dirpath, fn)
            try:
                st = os.stat(full)
            except OSError:
                continue
            rel = os.path.relpath(full, base)
            scanned += 1
            yield rel, st.st_size


def read_text_head(abs_path: str, max_bytes: int = READ_BYTES_PER_FILE) -> str:
    try:
        with open(abs_path, "rb") as f:
            data = f.read(max_bytes)
        # best-effort utf-8 decode
        return data.decode("utf-8", errors="replace")
    except Exception:
        return ""
