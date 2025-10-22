import os, re, json

# Parsing très simple des scripts Playwright générés par codegen (Python/TS)
# Objectif: extraire des steps atomiques pour process.json (MVP).

GOTO_RE_PY = re.compile(r"page\.goto\((['\"])(?P<url>.+?)\1")
CLICK_RE = re.compile(r"\)\.(?:dbl)?click\(")
DBLCLICK_RE = re.compile(r"\)\.dblclick\(")
FILL_RE = re.compile(r"\)\.fill\((['\"])(?P<text>.*?)\1")
PRESS_RE = re.compile(r"\)\.press\((['\"])(?P<key>.*?)\1")
WAIT_SEL_RE_PY = re.compile(r"page\.wait_for_selector\((['\"])(?P<sel>.+?)\1")
WAIT_TIMEOUT_RE_PY = re.compile(r"page\.wait_for_timeout\((?P<ms>\d+)\)")
SET_FILES_RE = re.compile(r"\)\.set_input_files\((?P<inside>[^)]*)\)")

GOTO_RE_TS = re.compile(r"await\s+page\.goto\((['\"])(?P<url>.+?)\1")
WAIT_SEL_RE_TS = re.compile(r"await\s+page\.waitForSelector\((['\"])(?P<sel>.+?)\1")
WAIT_TIMEOUT_RE_TS = re.compile(r"await\s+page\.waitForTimeout\((?P<ms>\d+)\)")


def _left_locator_source(line: str) -> str:
    # Retourne la chaîne avant .action( -> utilisée comme "selector" brut
    idx = line.find(').')
    if idx != -1:
        return line[: idx + 1].strip()
    # fallback: tout
    return line.strip()


def _parse_files_arg(arg_src: str) -> list:
    # Supporte: 'path', [ 'a', 'b' ]
    out = []
    s = arg_src.strip()
    if s.startswith('['):
        # liste
        try:
            # remplace quotes simples par doubles pour json.loads basique
            js = s.replace("'", '"')
            data = json.loads(js)
            if isinstance(data, list):
                out = [str(x) for x in data]
        except Exception:
            pass
    else:
        # chaîne simple 'path' ou "path"
        m = re.match(r"^(['\"])(?P<p>.+?)\1$", s)
        if m:
            out = [m.group('p')]
    return out


def parse_script_to_steps(text: str, language: str, chroot_abs: str) -> list:
    steps = []
    lines = text.splitlines()

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        # Python
        if language == 'playwright_python':
            m = GOTO_RE_PY.search(line)
            if m:
                steps.append({"action": "goto", "url": m.group('url')})
                continue
            if CLICK_RE.search(line):
                steps.append({"action": "click", "selector": _left_locator_source(line)})
                continue
            if DBLCLICK_RE.search(line):
                steps.append({"action": "dblclick", "selector": _left_locator_source(line)})
                continue
            m = FILL_RE.search(line)
            if m:
                steps.append({"action": "fill", "selector": _left_locator_source(line), "text": m.group('text')})
                continue
            m = PRESS_RE.search(line)
            if m:
                steps.append({"action": "press", "selector": _left_locator_source(line), "key": m.group('key')})
                continue
            m = WAIT_SEL_RE_PY.search(line)
            if m:
                steps.append({"action": "wait_for_selector", "selector": m.group('sel')})
                continue
            m = WAIT_TIMEOUT_RE_PY.search(line)
            if m:
                steps.append({"action": "wait_for_timeout", "timeout_ms": int(m.group('ms'))})
                continue
            m = SET_FILES_RE.search(line)
            if m:
                files = _parse_files_arg(m.group('inside'))
                files_rel = []
                for fp in files:
                    ap = os.path.abspath(fp if os.path.isabs(fp) else os.path.join(chroot_abs, fp))
                    # réécrire en chemin relatif si dans chroot
                    if ap.startswith(chroot_abs + os.sep):
                        files_rel.append(os.path.relpath(ap, chroot_abs))
                if files_rel:
                    steps.append({"action": "upload", "selector": _left_locator_source(line), "files": files_rel})
                continue
        else:
            # TS/JS basique
            m = GOTO_RE_TS.search(line)
            if m:
                steps.append({"action": "goto", "url": m.group('url')})
                continue
            if '.click(' in line and 'await ' in line:
                steps.append({"action": "click", "selector": _left_locator_source(line)})
                continue
            if '.dblclick(' in line and 'await ' in line:
                steps.append({"action": "dblclick", "selector": _left_locator_source(line)})
                continue
            if '.fill(' in line and 'await ' in line:
                # extraire texte
                m = re.search(r"\.fill\((['\"])(?P<text>.*?)\1\)", line)
                txt = m.group('text') if m else ''
                steps.append({"action": "fill", "selector": _left_locator_source(line), "text": txt})
                continue
            if '.press(' in line and 'await ' in line:
                m = re.search(r"\.press\((['\"])(?P<key>.*?)\1\)", line)
                key = m.group('key') if m else ''
                steps.append({"action": "press", "selector": _left_locator_source(line), "key": key})
                continue
            m = WAIT_SEL_RE_TS.search(line)
            if m:
                steps.append({"action": "wait_for_selector", "selector": m.group('sel')})
                continue
            m = WAIT_TIMEOUT_RE_TS.search(line)
            if m:
                steps.append({"action": "wait_for_timeout", "timeout_ms": int(m.group('ms'))})
                continue
            if '.setInputFiles(' in line and 'await ' in line:
                m = re.search(r"\.setInputFiles\((?P<i>[^)]*)\)", line)
                files_rel = []
                if m:
                    files = _parse_files_arg(m.group('i'))
                    for fp in files:
                        ap = os.path.abspath(fp if os.path.isabs(fp) else os.path.join(chroot_abs, fp))
                        if ap.startswith(chroot_abs + os.sep):
                            files_rel.append(os.path.relpath(ap, chroot_abs))
                if files_rel:
                    steps.append({"action": "upload", "selector": _left_locator_source(line), "files": files_rel})
                continue

    return steps
