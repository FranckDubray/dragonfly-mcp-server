from fnmatch import fnmatch
from typing import Iterable

def allowed_by_globs(path: str, includes: Iterable[str] | None, excludes: Iterable[str] | None) -> bool:
    if excludes:
        for g in excludes:
            try:
                if fnmatch(path, g):
                    return False
            except Exception:
                continue
    if includes:
        for g in includes:
            try:
                if fnmatch(path, g):
                    return True
            except Exception:
                continue
        return False
    return True
