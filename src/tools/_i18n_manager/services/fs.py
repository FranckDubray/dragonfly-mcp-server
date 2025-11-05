import os, glob, io, shutil, time

PROJECT_ROOT = os.path.abspath('.')

ALLOWED_EXTS = {'.json', '.js'}


def _safe_join(root_dir, *paths):
    base = os.path.abspath(os.path.join(PROJECT_ROOT, root_dir or ''))
    path = os.path.abspath(os.path.join(base, *paths))
    if not path.startswith(base):
        raise PermissionError('Path escape outside chroot is not allowed')
    return path


def glob_locales(root_dir, pattern):
    base = _safe_join(root_dir)
    pat = os.path.join(base, pattern or '*.{json,js}')
    # glob doesn't support brace expansion natively; implement simple union
    files = []
    if '{' in pat and '}' in pat:
        head, brace, tail = pat.partition('{')
        inner, close, rest = tail.partition('}')
        exts = inner.split(',')
        for ext in exts:
            files.extend(glob.glob(head + ext + rest, recursive=False))
    else:
        files = glob.glob(pat, recursive=False)
    # filter allowed extensions
    out = []
    for f in files:
        if os.path.isfile(f) and os.path.splitext(f)[1].lower() in ALLOWED_EXTS:
            out.append(f)
    return sorted(out)


def read_text(path):
    with io.open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write_atomic(path, content, backup=True):
    dir_name = os.path.dirname(path)
    base = os.path.basename(path)
    tmp = os.path.join(dir_name, '.' + base + '.tmp')
    if backup and os.path.exists(path):
        ts = time.strftime('%Y%m%d%H%M%S')
        shutil.copy2(path, path + f'.bak.{ts}')
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
