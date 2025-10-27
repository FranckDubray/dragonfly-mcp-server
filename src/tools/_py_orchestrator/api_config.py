
























from __future__ import annotations
from typing import Any, Dict, Tuple, List
import json
import pathlib
import pprint
import re

from .api_spawn import db_path_for_worker
from .db import get_state_kv, set_state_kv
from .validators import PY_WORKERS_DIR

# --- Helpers ---------------------------------------------------------------

def _tokenize_path(path: str) -> List[Tuple[str, Any]]:
    """Tokenize a path like: a.b[2].c[0]["x.y"] into a sequence of steps:
    [('key','a'), ('key','b'), ('idx',2), ('key','c'), ('idx',0), ('key','x.y')]
    Supports:
      - Dot notation for keys (no escaping)
      - Bracket numeric indices: [0]
      - Bracket quoted keys: ["..."] or ['...'] with \\-escaping inside quotes
    """
    s = str(path or '')
    n = len(s)
    i = 0
    toks: List[Tuple[str, Any]] = []
    while i < n:
        ch = s[i]
        if ch == '.':
            i += 1
            continue
        if ch == '[':
            i += 1
            while i < n and s[i].isspace():
                i += 1
            if i < n and s[i] in ('"', "'"):
                quote = s[i]
                i += 1
                buf = []
                while i < n:
                    c = s[i]
                    if c == '\\':
                        if i + 1 < n:
                            buf.append(s[i+1])
                            i += 2
                            continue
                        else:
                            i += 1
                            break
                    if c == quote:
                        i += 1
                        break
                    buf.append(c)
                    i += 1
                while i < n and s[i].isspace():
                    i += 1
                if i < n and s[i] == ']':
                    i += 1
                toks.append(('key', ''.join(buf)))
            else:
                while i < n and s[i].isspace():
                    i += 1
                numbuf = []
                while i < n and s[i].isdigit():
                    numbuf.append(s[i])
                    i += 1
                while i < n and s[i].isspace():
                    i += 1
                if i < n and s[i] == ']':
                    i += 1
                idx = int(''.join(numbuf)) if numbuf else 0
                toks.append(('idx', idx))
            continue
        buf = []
        while i < n and s[i] not in '.[':
            buf.append(s[i])
            i += 1
        if buf:
            toks.append(('key', ''.join(buf)))
    return toks


def _ensure_list_at(cur: list, index: int) -> list:
    if index < 0:
        index = 0
    while len(cur) <= index:
        cur.append(None)
    return cur


def _assign_by_tokens(node: Any, tokens: List[Tuple[str, Any]], value: Any) -> Any:
    if not tokens:
        return value
    kind, val = tokens[0]
    last = (len(tokens) == 1)
    if kind == 'key':
        if not isinstance(node, dict):
            node = {}
        if last:
            node[val] = value
            return node
        child = node.get(val)
        node[val] = _assign_by_tokens(child, tokens[1:], value)
        return node
    else:
        idx = int(val)
        if not isinstance(node, list):
            node = []
        node = _ensure_list_at(node, idx)
        if last:
            node[idx] = value
            return node
        node[idx] = _assign_by_tokens(node[idx], tokens[1:], value)
        return node


def _delete_by_tokens(node: Any, tokens: List[Tuple[str, Any]]) -> Any:
    if not tokens:
        return node
    kind, val = tokens[0]
    last = (len(tokens) == 1)
    if kind == 'key':
        if not isinstance(node, dict):
            return node
        if last:
            try:
                node.pop(val, None)
            except Exception:
                pass
            return node
        if val in node:
            node[val] = _delete_by_tokens(node[val], tokens[1:])
        return node
    else:
        # idx
        if not isinstance(node, list):
            return node
        idx = int(val)
        if idx < 0 or idx >= len(node):
            return node
        if last:
            # Do not shift indexes: set None
            node[idx] = None
            return node
        node[idx] = _delete_by_tokens(node[idx], tokens[1:])
        return node


def _set_by_path(obj: Any, path: str, value: Any) -> Any:
    toks = _tokenize_path(path)
    if not toks:
        return obj
    if obj is None:
        obj = {} if toks[0][0] == 'key' else []
    return _assign_by_tokens(obj, toks, value)


def _del_by_path(obj: Any, path: str) -> Any:
    toks = _tokenize_path(path)
    if not toks:
        return obj
    return _delete_by_tokens(obj, toks)


def _persist_config_file_top(worker_name: str, key: str, value: Any) -> bool:
    try:
        cfg_path = pathlib.Path(PY_WORKERS_DIR) / worker_name / 'config.py'
        if not cfg_path.is_file():
            return False
        src = cfg_path.read_text(encoding='utf-8')
        ns: Dict[str, Any] = {}
        try:
            exec(compile(src, str(cfg_path), 'exec'), {}, ns)
        except Exception:
            pass
        cfg = None
        for k in ('CONFIG', 'WORKER_CONFIG', 'config'):
            if isinstance(ns.get(k), dict):
                cfg = dict(ns.get(k))
                break
        if cfg is None:
            cfg = {}
        if value is None:
            try:
                cfg.pop(key, None)
            except Exception:
                pass
        else:
            cfg[key] = value
        cfg_repr = pprint.pformat(cfg, width=100, sort_dicts=False)
        new_block = f"CONFIG = {cfg_repr}\n\n"
        pattern = re.compile(r"CONFIG\s*=\s*\{[\s\S]*?\}\s*\n", flags=re.MULTILINE)
        if pattern.search(src):
            new_src = pattern.sub(new_block, src, count=1)
        else:
            new_src = src.rstrip() + "\n\n" + new_block
        cfg_path.write_text(new_src, encoding='utf-8')
        return True
    except Exception:
        return False


def _write_under_config_dir(worker_name: str, rel_path: str, value: Any) -> bool:
    try:
        base_dir = pathlib.Path(PY_WORKERS_DIR) / worker_name / 'config'
        target = (base_dir / rel_path).resolve()
        if not str(target).startswith(str(base_dir.resolve())):
            return False
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(value, (dict, list)):
            content = json.dumps(value, ensure_ascii=False, indent=2)
        else:
            content = str(value) if value is not None else ''
        with open(target, 'w', encoding='utf-8') as fh:
            fh.write(content)
        return True
    except Exception:
        return False


def _auto_file_route_for_key_path(key_path: str) -> Tuple[bool, str]:
    try:
        if not key_path:
            return False, ''
        parts = _tokenize_path(key_path)
        if len(parts) == 2 and parts[0] == ('key', 'prompts') and parts[1][0] == 'key':
            name = parts[1][1]
            return True, f"prompts/{name}.md"
    except Exception:
        pass
    return False, ''

# JSON config.json helpers

def _config_json_path(worker_name: str) -> pathlib.Path:
    return (pathlib.Path(PY_WORKERS_DIR) / worker_name / 'config' / 'config.json').resolve()


def _read_config_json(worker_name: str) -> Dict[str, Any]:
    p = _config_json_path(worker_name)
    if p.is_file():
        try:
            return json.loads(p.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}


def _write_config_json(worker_name: str, obj: Dict[str, Any]) -> bool:
    try:
        p = _config_json_path(worker_name)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
        return True
    except Exception:
        return False

# --- Operation -------------------------------------------------------------

def config_op(params: dict) -> dict:
    wn = (params or {}).get('worker_name')
    if not wn:
        return {"accepted": False, "status": "error", "message": "worker_name required", "truncated": False}

    dbp = db_path_for_worker(wn)

    set_req = (params or {}).get('set') or {}
    changed = False
    file_persisted = False

    # Update path
    if isinstance(set_req, dict) and (set_req.get('key') is not None or set_req.get('key_path') is not None or set_req.get('file') is not None):
        # Load current metadata from KV
        try:
            raw_md = get_state_kv(dbp, wn, 'py.process_metadata') or '{}'
            md = json.loads(raw_md)
        except Exception:
            md = {}

        # Priority: explicit file write under config/
        file_rel = set_req.get('file')
        if isinstance(file_rel, str) and file_rel:
            ok = _write_under_config_dir(wn, file_rel, set_req.get('value'))
            changed = changed or ok
            file_persisted = file_persisted or ok
        else:
            key_path = set_req.get('key_path')
            remove_flag = bool(set_req.get('remove'))
            if isinstance(key_path, str) and key_path:
                storage = (set_req.get('storage') or 'file').lower()
                auto, auto_rel = _auto_file_route_for_key_path(key_path)
                if storage == 'file':
                    if auto and not remove_flag:
                        ok = _write_under_config_dir(wn, auto_rel, set_req.get('value'))
                        file_persisted = file_persisted or ok
                    else:
                        cfg = _read_config_json(wn)
                        if remove_flag:
                            cfg = _del_by_path(cfg, key_path)
                        else:
                            cfg = _set_by_path(cfg, key_path, set_req.get('value'))
                        ok = _write_config_json(wn, cfg)
                        file_persisted = file_persisted or ok
                # Always reflect in KV mirror (metadata)
                if remove_flag:
                    md = _del_by_path(md, key_path)
                else:
                    md = _set_by_path(md, key_path, set_req.get('value'))
                changed = True
            else:
                # Shallow key write/remove
                k = str(set_req.get('key')) if set_req.get('key') is not None else None
                if k is not None:
                    if bool(set_req.get('remove')):
                        try:
                            md.pop(k, None)
                        except Exception:
                            pass
                        changed = True
                        file_persisted = _persist_config_file_top(wn, k, None) or file_persisted
                    else:
                        v = set_req.get('value')
                        md[k] = v
                        changed = True
                        file_persisted = _persist_config_file_top(wn, k, v) or file_persisted

        # Persist KV mirror
        if changed:
            try:
                set_state_kv(dbp, wn, 'py.process_metadata', json.dumps(md))
            except Exception:
                pass

    # Read path
    try:
        raw_md = get_state_kv(dbp, wn, 'py.process_metadata') or '{}'
        md = json.loads(raw_md)
    except Exception:
        md = {}
    try:
        raw_docs = get_state_kv(dbp, wn, 'py.process_config_docs') or '{}'
        docs = json.loads(raw_docs)
    except Exception:
        docs = {}

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

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
