import os, json, re
from typing import Any, Dict, Optional

# Chroot racine pour tous les fichiers Playwright
CHROOT = os.path.join(os.getcwd(), 'playwright')


def safe_path(*parts: str) -> str:
    base = os.path.abspath(CHROOT)
    out = os.path.abspath(os.path.join(base, *parts))
    if not out.startswith(base + os.sep) and out != base:
        raise ValueError("Chemin hors chroot playwright/")
    return out


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def write_atomic(path: str, data: Dict) -> None:
    tmp = path + ".tmp"
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def abs_from_rel(rel: str) -> str:
    return safe_path(rel)


# --- Gestion TMP chrooté + HOME + browsers path ---

def set_tmp_env_for_recording(rec_dir: str) -> Dict[str, Optional[str]]:
    tmpdir = os.path.join(rec_dir, 'tmp')
    homedir = os.path.join(tmpdir, 'home')
    browsers_dir = os.path.join(CHROOT, 'browsers')
    ensure_dir(tmpdir)
    ensure_dir(homedir)
    ensure_dir(browsers_dir)

    keys = ('TMPDIR', 'TEMP', 'TMP', 'HOME', 'USERPROFILE', 'PLAYWRIGHT_BROWSERS_PATH')
    prev: Dict[str, Optional[str]] = {k: os.environ.get(k) for k in keys}

    os.environ['TMPDIR'] = tmpdir
    os.environ['TEMP'] = tmpdir
    os.environ['TMP'] = tmpdir
    os.environ['HOME'] = homedir  # Unix/macOS
    os.environ['USERPROFILE'] = homedir  # Windows fallback si utilisé
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = browsers_dir

    return prev


def restore_tmp_env(prev_env: Dict[str, Optional[str]]) -> None:
    try:
        for k, v in prev_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    except Exception:
        pass


# --- Résolution des locators (whitelist de méthodes usuelles) ---

def _apply_call(obj: Any, call_src: str):
    name_end = call_src.find('(')
    if name_end == -1:
        raise ValueError(f"Appel invalide dans selector: {call_src}")
    name = call_src[:name_end].strip()
    args_src = call_src[name_end + 1 :].rstrip(')')

    def _first_str(pattern: str) -> Optional[str]:
        m = re.search(pattern, args_src)
        return m.group(1) if m else None

    if name == 'locator':
        s = _first_str(r'''["'](.*?)["']''')
        if s is None:
            raise ValueError("locator(...) sans chaîne")
        return obj.locator(s)

    if name == 'get_by_role':
        role = _first_str(r'''get_by_role\(\s*["'](.*?)["']''')
        nm = _first_str(r'''name\s*=\s*["'](.*?)["']''')
        return obj.get_by_role(role, name=nm) if nm else obj.get_by_role(role)

    if name == 'get_by_text':
        s = _first_str(r'''["'](.*?)["']''')
        return obj.get_by_text(s)
    if name == 'get_by_label':
        s = _first_str(r'''["'](.*?)["']''')
        return obj.get_by_label(s)
    if name == 'get_by_placeholder':
        s = _first_str(r'''["'](.*?)["']''')
        return obj.get_by_placeholder(s)
    if name == 'get_by_test_id':
        s = _first_str(r'''["'](.*?)["']''')
        return obj.get_by_test_id(s)

    raise ValueError(f"Méthode non supportée dans selector: {name}")


def resolve_locator(page, selector_src: str):
    src = selector_src.strip()
    if src.startswith('page.'):
        src = src[5:]
    parts = []
    buf = src
    while buf:
        idx = buf.find(').')
        if idx == -1:
            parts.append(buf)
            break
        parts.append(buf[: idx + 1])
        buf = buf[idx + 2 :]
    obj = page
    for call_src in parts:
        obj = _apply_call(obj, call_src)
    return obj
