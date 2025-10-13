import os
from typing import Tuple


def resolve_root_and_abs(root: str, rel: str) -> Tuple[str, str]:
    base = os.path.abspath(root)
    abs_path = os.path.abspath(os.path.join(base, rel))
    if not abs_path.startswith(base):
        raise ValueError("Path escapes repository root")
    return base, abs_path
