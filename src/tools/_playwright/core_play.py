import os, json, subprocess, sys
from datetime import datetime
from .utils import CHROOT, ensure_dir, safe_path, abs_from_rel, set_tmp_env_for_recording, restore_tmp_env, resolve_locator
from .parser import parse_script_to_steps

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    _PW_OK = True
except Exception:
    _PW_OK = False


def _snap(page, images_dir: str, tag: str, idx: int) -> str:
    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]
    fname = f"{ts}_step_{idx:03d}_{tag}.png"
    out = os.path.join(images_dir, fname)
    page.screenshot(path=out, full_page=True)
    return out


def _ensure_process_json(rec_dir: str) -> str:
    pj_path = os.path.join(rec_dir, 'process.json')
    need_generate = True
    if os.path.isfile(pj_path):
        try:
            with open(pj_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict) and isinstance(data.get('steps'), list) and len(data['steps']) > 0:
                need_generate = False
        except Exception:
            pass
    if not need_generate:
        return pj_path

    script_py = os.path.join(rec_dir, 'script.py')
    script_ts = os.path.join(rec_dir, 'script.ts')
    script_path = script_py if os.path.isfile(script_py) else (script_ts if os.path.isfile(script_ts) else None)
    if not script_path:
        with open(pj_path, 'w', encoding='utf-8') as f:
            json.dump({"version": "pw-steps-1", "steps": []}, f)
        return pj_path

    language = 'playwright_python' if script_path.endswith('.py') else 'playwright_ts'
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            text = f.read()
        steps = parse_script_to_steps(text, language, os.path.abspath(CHROOT))
        with open(pj_path, 'w', encoding='utf-8') as f:
            json.dump({"version": "pw-steps-1", "steps": steps}, f, ensure_ascii=False, indent=2)
    except Exception:
        try:
            with open(pj_path, 'w', encoding='utf-8') as f:
                json.dump({"version": "pw-steps-1", "steps": []}, f)
        except Exception:
            pass
    return pj_path


def play_run(p: dict):
    rid = p['recording_id']
    raw_script = bool(p.get('raw_script', False))

    if raw_script:
        # Exécuter directement le script Playwright généré
        rec_dir = safe_path(rid)
        script_py = os.path.join(rec_dir, 'script.py')
        if not os.path.isfile(script_py):
            return {"ok": False, "error": "script.py introuvable pour cet ID"}
        env = os.environ.copy()
        # Confinement TMP/HOME
        prev_env = set_tmp_env_for_recording(rec_dir)
        try:
            # Lancer le script avec le Python courant
            proc = subprocess.run([sys.executable, script_py], cwd=CHROOT, capture_output=True, text=True, timeout=600)
            out = proc.stdout[-4000:] if proc.stdout else ""
            err = proc.stderr[-4000:] if proc.stderr else ""
            return {
                "ok": proc.returncode == 0,
                "recording_id": rid,
                "mode": "raw_script",
                "exit_code": proc.returncode,
                "stdout_tail": out,
                "stderr_tail": err,
            }
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "raw_script timeout (600s)"}
        except Exception as e:
            return {"ok": False, "error": f"raw_script error: {e}"}
        finally:
            restore_tmp_env(prev_env)

    # Sinon: exécution par étapes (screenshots before/after)
    mode = p.get('mode', 'run_all')
    tsi = p.get('target_step_index')
    headless = bool(p.get('play_headless', True))
    slow_mo = int(p.get('slow_mo_ms', 0))
    default_timeout = int(p.get('timeout_ms', 10000))
    screenshot_on_failure = bool(p.get('screenshot_on_failure', True))
    limit = int(p.get('limit', 50))

    rec_dir = safe_path(rid)
    pj_path = _ensure_process_json(rec_dir)
    if not os.path.isfile(pj_path):
        raise ValueError('process.json introuvable pour cet ID (et aucun script.* pour le générer)')
    with open(pj_path, 'r', encoding='utf-8') as f:
        proc = json.load(f)

    steps = proc.get('steps', [])
    total = len(steps)
    if total == 0:
        return {"ok": True, "recording_id": rid, "steps_executed": 0, "total_steps": 0, "message": "Aucune étape"}

    run_until = total - 1 if mode == 'run_all' else min(tsi if isinstance(tsi, int) else 0, total - 1)

    images_dir = os.path.join(rec_dir, 'images')
    ensure_dir(images_dir)
    ensure_dir(os.path.join(rec_dir, 'tmp'))

    logs, executed = [], 0

    if not _PW_OK:
        logs.append('Playwright indisponible (import). Exécution simulée.')
        for i in range(run_until + 1):
            logs.append(f"Would execute step {i}: {steps[i].get('action')}")
        returned = logs[:limit]
        return {
            "ok": True,
            "recording_id": rid,
            "mode": mode,
            "steps_executed": run_until + 1,
            "total_steps": total,
            "failed_step": None,
            "images_dir": os.path.relpath(images_dir, CHROOT),
            "logs": {
                "returned_count": len(returned),
                "total_count": len(logs),
                "truncated": len(logs) > len(returned),
                "items": returned,
                "message": "Logs tronqués" if len(logs) > len(returned) else None,
            },
        }

    prev_env = None
    try:
        prev_env = set_tmp_env_for_recording(rec_dir)
        with sync_playwright() as pw:
            user_data = os.path.join(rec_dir, 'tmp', 'profile')
            ensure_dir(user_data)
            ctx = pw.chromium.launch_persistent_context(user_data, headless=headless, slow_mo=slow_mo or 0, accept_downloads=True)
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.set_default_timeout(default_timeout)

            for i in range(run_until + 1):
                step = steps[i]
                action = step.get('action')
                try:
                    _snap(page, images_dir, 'before', i)
                    if action == 'goto':
                        url = step.get('url')
                        if not url:
                            raise ValueError('goto: url manquant')
                        page.goto(url)
                    elif action in ('click', 'dblclick'):
                        loc = resolve_locator(page, step.get('selector', ''))
                        (loc.click() if action == 'click' else loc.dblclick())
                    elif action == 'fill':
                        loc = resolve_locator(page, step.get('selector', ''))
                        loc.fill(step.get('text', ''))
                    elif action == 'type':
                        loc = resolve_locator(page, step.get('selector', ''))
                        loc.type(step.get('text', ''))
                    elif action == 'press':
                        loc = resolve_locator(page, step.get('selector', ''))
                        loc.press(step.get('key', ''))
                    elif action == 'wait_for_selector':
                        page.wait_for_selector(step.get('selector', ''))
                    elif action == 'wait_for_timeout':
                        page.wait_for_timeout(int(step.get('timeout_ms', default_timeout)))
                    elif action == 'upload':
                        loc = resolve_locator(page, step.get('selector', ''))
                        files = [abs_from_rel(fp) for fp in step.get('files', [])]
                        loc.set_input_files(files)
                    else:
                        logs.append(f"Step {i}: action non supportée: {action}")
                    _snap(page, images_dir, 'after', i)
                    executed = i + 1
                except PWTimeout as te:
                    try: _snap(page, images_dir, 'error', i)
                    except Exception: pass
                    return _result(rid, mode, executed, total, images_dir, logs, limit, failed=i, err=str(te))
                except Exception as e:
                    try: _snap(page, images_dir, 'error', i)
                    except Exception: pass
                    return _result(rid, mode, executed, total, images_dir, logs, limit, failed=i, err=str(e))
            ctx.close()
    except Exception as e:
        return {"ok": False, "error": f"Playwright runtime error: {e}"}
    finally:
        if prev_env is not None:
            restore_tmp_env(prev_env)

    return _result(rid, mode, executed, total, images_dir, logs, limit, failed=None)


def _result(rid, mode, executed, total, images_dir, logs, limit, failed=None, err=None):
    returned = logs[:limit]
    return {
        "ok": failed is None,
        "recording_id": rid,
        "mode": mode,
        "steps_executed": executed,
        "total_steps": total,
        "failed_step": failed,
        "error": err,
        "images_dir": os.path.relpath(images_dir, CHROOT),
        "logs": {
            "returned_count": len(returned),
            "total_count": len(logs),
            "truncated": len(logs) > len(returned),
            "items": returned,
            "message": "Logs tronqués" if len(logs) > len(returned) else None,
        },
    }
