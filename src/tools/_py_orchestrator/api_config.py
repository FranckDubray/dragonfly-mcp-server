












from __future__ import annotations
from typing import Any, Dict

from .api_spawn import db_path_for_worker
from .db import get_state_kv, set_state_kv
from .validators import PY_WORKERS_DIR

# NEW split modules
from .config_fs import (
    scan_config_dir,
    write_under_config_dir,
    read_config_json,
    write_config_json,
    auto_file_route_for_key_path,
    set_key_file,
)
from .config_path_utils import persist_config_file_top


def config_op(params: dict) -> dict:
    wn = (params or {}).get('worker_name')
    if not wn:
        return {"accepted": False, "status": "error", "message": "worker_name required", "truncated": False}

    set_req = (params or {}).get('set') or {}
    changed = False
    file_persisted = False

    # WRITE (file-first)
    if isinstance(set_req, dict) and (set_req.get('key') is not None or set_req.get('key_path') is not None or set_req.get('file') is not None):
        file_rel = set_req.get('file')
        if isinstance(file_rel, str) and file_rel:
            ok = write_under_config_dir(wn, file_rel, set_req.get('value'))
            changed = changed or ok
            file_persisted = file_persisted or ok
        else:
            key_path = set_req.get('key_path')
            remove_flag = bool(set_req.get('remove'))
            if isinstance(key_path, str) and key_path:
                storage = (set_req.get('storage') or 'file').lower()
                auto, auto_rel = auto_file_route_for_key_path(key_path)
                if storage == 'file':
                    if auto and not remove_flag:
                        ok = write_under_config_dir(wn, auto_rel, set_req.get('value'))
                        file_persisted = file_persisted or ok
                        changed = changed or ok
                    else:
                        ok = set_key_file(wn, key_path, set_req.get('value'), remove_flag)
                        file_persisted = file_persisted or ok
                        changed = changed or ok
                else:
                    # inline → KV only (legacy)
                    dbp = db_path_for_worker(wn)
                    try:
                        import json
                        raw_md = get_state_kv(dbp, wn, 'py.process_metadata') or '{}'
                        md = json.loads(raw_md)
                    except Exception:
                        md = {}
                    if remove_flag:
                        from .config_path_utils import del_by_path
                        md = del_by_path(md, key_path)
                    else:
                        from .config_path_utils import set_by_path
                        md = set_by_path(md, key_path, set_req.get('value'))
                    try:
                        set_state_kv(dbp, wn, 'py.process_metadata', json.dumps(md))
                    except Exception:
                        pass
                    changed = True
            else:
                # shallow top-level key
                k = str(set_req.get('key')) if set_req.get('key') is not None else None
                if k is not None:
                    cfg = read_config_json(wn)
                    if bool(set_req.get('remove')):
                        try:
                            cfg.pop(k, None)
                        except Exception:
                            pass
                        changed = True
                    else:
                        v = set_req.get('value')
                        cfg[k] = v
                        changed = True
                    file_persisted = write_config_json(wn, cfg) or file_persisted
                    # best-effort optional top-level config.py
                    from pathlib import Path
                    persist_config_file_top(Path(PY_WORKERS_DIR)/wn, k, None if bool(set_req.get('remove')) else v)

        # Optional mirror to KV after write (best-effort)
        if changed:
            try:
                import json
                dbp = db_path_for_worker(wn)
                md_scan, docs_scan = scan_config_dir(wn)
                set_state_kv(dbp, wn, 'py.process_metadata', json.dumps(md_scan))
                if docs_scan:
                    set_state_kv(dbp, wn, 'py.process_config_docs', json.dumps(docs_scan))
            except Exception:
                pass

    # READ: pure FS scan (works offline)
    md, docs = scan_config_dir(wn)

    return {
        "accepted": True,
        "status": "ok",
        "worker_name": wn,
        "metadata": md,
        "docs": docs,
        "changed": changed,
        "file_persisted": bool(file_persisted),
        "truncated": False,
    }
