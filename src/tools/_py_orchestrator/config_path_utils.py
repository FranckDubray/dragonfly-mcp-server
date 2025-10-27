from __future__ import annotations
from typing import Any, Dict, List, Tuple
import pprint
import re

# Path tokenization and JSON set/delete helpers

def tokenize_path(path: str) -> List[Tuple[str, Any]]:
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


def set_by_path(obj: Any, path: str, value: Any) -> Any:
    toks = tokenize_path(path)
    if not toks:
        return obj
    if obj is None:
        obj = {} if toks[0][0] == 'key' else []
    return _assign_by_tokens(obj, toks, value)


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


def del_by_path(obj: Any, path: str) -> Any:
    toks = tokenize_path(path)
    if not toks:
        return obj
    return _delete_by_tokens(obj, toks)


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
        if not isinstance(node, list):
            return node
        idx = int(val)
        if idx < 0 or idx >= len(node):
            return node
        if last:
            node[idx] = None
            return node
        node[idx] = _delete_by_tokens(node[idx], tokens[1:])
        return node


# For optional top-level config.py updates (best-effort)
import pathlib

def persist_config_file_top(worker_root: pathlib.Path, key: str, value: Any) -> bool:
    try:
        cfg_path = worker_root / 'config.py'
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
