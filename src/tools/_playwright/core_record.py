import os, json, shutil, subprocess, sys, threading, time
from datetime import datetime
from .parser import parse_script_to_steps

CHROOT = os.path.join(os.getcwd(), 'playwright')


def _safe_path(*parts):
    base = os.path.abspath(CHROOT)
    out = os.path.abspath(os.path.join(base, *parts))
    if not out.startswith(base + os.sep) and out != base:
        raise ValueError("Chemin hors chroot playwright/")
    return out


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def _write_atomic(path: str, data: dict):
    tmp = path + ".tmp"
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _record_dir(recording_id: str) -> str:
    return _safe_path(recording_id)


def _script_path(recording_id: str, target: str) -> str:
    ext = 'py' if target == 'playwright_python' else 'ts'
    return os.path.join(_record_dir(recording_id), f'script.{ext}')


def _process_json_path(recording_id: str) -> str:
    return os.path.join(_record_dir(recording_id), 'process.json')


def _finalize_process_json(rec_dir: str, script_path: str):
    if not os.path.isfile(script_path):
        return
    language = 'playwright_python' if script_path.endswith('.py') else 'playwright_ts'
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            text = f.read()
        steps = parse_script_to_steps(text, language, os.path.abspath(CHROOT))
        data = {"version": "pw-steps-1", "steps": steps}
        _write_atomic(os.path.join(rec_dir, 'process.json'), data)
    except Exception:
        pass


def _start_finalizer_thread(proc: subprocess.Popen, rec_dir: str, script_path: str, pidfile: str):
    def _worker():
        rc = None
        try:
            rc = proc.wait()
        except Exception:
            pass
        try:
            _finalize_process_json(rec_dir, script_path)
        except Exception:
            pass
        try:
            meta = {}
            if os.path.isfile(pidfile):
                with open(pidfile, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
            meta['ended_at'] = datetime.utcnow().isoformat() + 'Z'
            meta['exit_code'] = rc
            with open(pidfile, 'w', encoding='utf-8') as f:
                json.dump(meta, f)
        except Exception:
            pass

    t = threading.Thread(target=_worker, name="pw_codegen_finalizer", daemon=True)
    t.start()


def _preflight_check() -> tuple[bool, str | None]:
    """Vérifie rapidement que le CLI Playwright Python est disponible."""
    try:
        res = subprocess.run([sys.executable, "-m", "playwright", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        if res.returncode != 0:
            return False, res.stderr.decode(errors='ignore')[:300]
        return True, None
    except Exception as e:
        return False, str(e)


def _dir_non_empty(path: str) -> bool:
    try:
        return os.path.isdir(path) and any(os.scandir(path))
    except Exception:
        return False


def record_start(p: dict):
    rid = p['recording_id']
    overwrite = bool(p.get('overwrite', False))
    start_url = p.get('start_url')
    target = p.get('target', 'playwright_python')
    headless = bool(p.get('record_headless', False))

    # S'assurer que le chroot existe
    _ensure_dir(CHROOT)

    # Pré-créer le répertoire d'enregistrement (stateless, même si codegen échoue)
    rec_dir = _record_dir(rid)
    if os.path.isdir(rec_dir):
        if not overwrite:
            raise ValueError("Enregistrement existe déjà (utiliser overwrite=true)")
        # refuser si un pid actif est présent
        pidfile = os.path.join(rec_dir, 'pid.json')
        if os.path.isfile(pidfile):
            with open(pidfile, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            pid = meta.get('pid')
            if pid and _pid_alive(pid):
                raise ValueError("Processus codegen actif détecté: impossible d'écraser")
        shutil.rmtree(rec_dir)
    _ensure_dir(rec_dir)
    _ensure_dir(os.path.join(rec_dir, 'uploads'))
    _ensure_dir(os.path.join(rec_dir, 'artifacts'))
    _ensure_dir(os.path.join(rec_dir, 'storage'))
    _ensure_dir(os.path.join(rec_dir, 'tmp'))

    # init process.json minimal (sera remplacé à la fermeture)
    pj_path = _process_json_path(rid)
    if not os.path.exists(pj_path):
        _write_atomic(pj_path, {"version": "pw-steps-1", "steps": []})

    # Préflight CLI Playwright Python
    ok_cli, cli_err = _preflight_check()
    if not ok_cli:
        return {
            "ok": False,
            "error": "Playwright CLI Python indisponible",
            "hint": "Installez les dépendances: pip install -e . puis python -m playwright install chromium",
            "details": cli_err,
        }

    # Construire la commande codegen
    script_path = _script_path(rid, target)
    args = [sys.executable, "-m", "playwright", "codegen"]
    if headless:
        args += ["--headless"]
    if target == 'playwright_python':
        args += ["--target", "python"]
    else:
        args += ["--target", "javascript"]
    args += ["--output", script_path]
    if start_url:
        args += [start_url]

    # Isolation env (TMP uniquement sous chroot; HOME conservé pour compat macOS GUI)
    env = os.environ.copy()
    tmpdir = os.path.join(rec_dir, 'tmp')
    browsers_dir = os.path.join(CHROOT, 'browsers')
    _ensure_dir(tmpdir)
    _ensure_dir(browsers_dir)
    env['TMPDIR'] = tmpdir
    env['TEMP'] = tmpdir
    env['TMP'] = tmpdir
    # Ne définir PLAYWRIGHT_BROWSERS_PATH que si des navigateurs sont installés dedans
    if _dir_non_empty(browsers_dir):
        env['PLAYWRIGHT_BROWSERS_PATH'] = browsers_dir

    # Lancer codegen
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
    preexec_fn = None if sys.platform == 'win32' else os.setsid

    try:
        proc = subprocess.Popen(
            args,
            cwd=CHROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
            preexec_fn=preexec_fn,
            env=env,
        )
    except Exception as e:
        return {"ok": False, "error": f"Echec lancement codegen: {e}"}

    # Écrire pid.json immédiatement
    pidfile = os.path.join(rec_dir, 'pid.json')
    with open(pidfile, 'w', encoding='utf-8') as f:
        json.dump({"pid": proc.pid, "started_at": datetime.utcnow().isoformat() + 'Z', "args": args}, f)

    # Vérifier démarrage effectif (process vivant après court délai)
    time.sleep(0.8)
    if proc.poll() is not None:
        # Process déjà terminé → fournir un message explicite et des hints
        hints = [
            "Vérifiez l'installation des navigateurs: python -m playwright install chromium",
            "Assurez-vous que le serveur tourne dans une session utilisateur GUI (Terminal ouvert), pas en service headless",
            "Essayez record_headless:true si aucune GUI n'est disponible",
        ]
        if not _dir_non_empty(browsers_dir):
            hints.insert(0, "Option confinement: PLAYWRIGHT_BROWSERS_PATH=playwright/browsers python -m playwright install chromium")
        return {
            "ok": False,
            "error": "Playwright codegen s'est terminé immédiatement (pas de fenêtre ouverte)",
            "hints": hints,
            "exit_code": proc.returncode,
            "paths": {
                "dir": os.path.relpath(rec_dir, CHROOT),
                "script": os.path.relpath(script_path, CHROOT),
                "process_json": os.path.relpath(pj_path, CHROOT),
            },
        }

    # Thread finaliseur à la fermeture
    _start_finalizer_thread(proc, rec_dir, script_path, pidfile)

    return {
        "ok": True,
        "recording_id": rid,
        "started": True,
        "paths": {
            "dir": os.path.relpath(rec_dir, CHROOT),
            "script": os.path.relpath(script_path, CHROOT),
            "process_json": os.path.relpath(pj_path, CHROOT),
        },
        "note": "Fermez la fenêtre Playwright pour finaliser l'enregistrement. process.json est généré automatiquement à la fermeture.",
    }


def record_list(p: dict):
    limit = int(p.get('limit', 50))
    base = CHROOT
    if not os.path.isdir(base):
        return {"ok": True, "total_count": 0, "returned_count": 0, "truncated": False, "items": []}

    items = []
    for name in sorted(os.listdir(base)):
        d = os.path.join(base, name)
        if os.path.isdir(d):
            pj = os.path.join(d, 'process.json')
            steps = None
            if os.path.isfile(pj):
                try:
                    with open(pj, 'r', encoding='utf-8') as f:
                        steps = len(json.load(f).get('steps', []))
                except Exception:
                    steps = None
            items.append({"id": name, "steps_count": steps})

    total = len(items)
    ret = items[:limit]
    return {
        "ok": True,
        "total_count": total,
        "returned_count": len(ret),
        "truncated": total > len(ret),
        "items": ret,
        "message": "Liste tronquée" if total > len(ret) else None,
    }


def record_delete(p: dict):
    rid = p['recording_id']
    rec_dir = _record_dir(rid)
    if not os.path.isdir(rec_dir):
        return {"ok": True, "recording_id": rid, "deleted": False, "message": "Aucun enregistrement"}
    pidfile = os.path.join(rec_dir, 'pid.json')
    if os.path.isfile(pidfile):
        try:
            with open(pidfile, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            pid = meta.get('pid')
            if pid and _pid_alive(pid):
                raise ValueError("Processus codegen actif: fermer la fenêtre avant suppression")
        except Exception:
            pass
    shutil.rmtree(rec_dir)
    return {"ok": True, "recording_id": rid, "deleted": True}


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False
