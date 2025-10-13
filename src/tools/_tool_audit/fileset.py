from __future__ import annotations
import os
from typing import List

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


EXCLUDE_DIRS = {"__pycache__", ".git", "node_modules", ".venv", "dist", "build", "sqlite3", "assets"}
EXCLUDE_EXT = {".pyc"}


def collect_tool_files(tool_name: str) -> List[str]:
    files: List[str] = []
    # bootstrap
    bootstrap = os.path.join(ROOT, "src", "tools", f"{tool_name}.py")
    if os.path.isfile(bootstrap):
        files.append(bootstrap)
    # spec
    spec = os.path.join(ROOT, "src", "tool_specs", f"{tool_name}.json")
    if os.path.isfile(spec):
        files.append(spec)
    # package
    pkg_dir = os.path.join(ROOT, "src", "tools", f"_{tool_name}")
    if os.path.isdir(pkg_dir):
        for root, dirs, filenames in os.walk(pkg_dir):
            # prune excluded dirs
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for fn in filenames:
                _, ext = os.path.splitext(fn)
                if ext in EXCLUDE_EXT:
                    continue
                path = os.path.join(root, fn)
                files.append(path)
    return files
