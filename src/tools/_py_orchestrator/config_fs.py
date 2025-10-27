from __future__ import annotations
from typing import Any, Dict, Tuple
import json
import pathlib

from .validators import PY_WORKERS_DIR
from .config_path_utils import set_by_path, del_by_path


def config_json_path(worker_name: str) -> pathlib.Path:
    return (pathlib.Path(PY_WORKERS_DIR) / worker_name / 'config' / 'config.json').resolve()


def read_config_json(worker_name: str) -> Dict[str, Any]:
    p = config_json_path(worker_name)
    if p.is_file():
        try:
            return json.loads(p.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}


def write_config_json(worker_name: str, obj: Dict[str, Any]) -> bool:
    try:
        p = config_json_path(worker_name)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
        return True
    except Exception:
        return False


def write_under_config_dir(worker_name: str, rel_path: str, value: Any) -> bool:
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


def auto_file_route_for_key_path(key_path: str) -> Tuple[bool, str]:
    try:
        from .config_path_utils import tokenize_path
        parts = tokenize_path(key_path)
        if len(parts) == 2 and parts[0] == ('key', 'prompts') and parts[1][0] == 'key':
            name = parts[1][1]
            return True, f"prompts/{name}.md"
    except Exception:
        pass
    return False, ''


def scan_config_dir(worker_name: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    metadata: Dict[str, Any] = {}
    base = pathlib.Path(PY_WORKERS_DIR) / worker_name / 'config'
    # config.json
    cfg = read_config_json(worker_name)
    if isinstance(cfg, dict):
        metadata.update(cfg)
    # prompts
    prompts_dir = base / 'prompts'
    if prompts_dir.is_dir():
        for p in sorted(prompts_dir.glob('*')):
            if p.suffix.lower() in {'.md', '.txt'} and p.is_file():
                try:
                    txt = p.read_text(encoding='utf-8')
                except Exception:
                    txt = ''
                metadata.setdefault('prompts', {})[p.stem] = txt
    # docs
    docs: Dict[str, Any] = {}
    # NEW: scan all *.py recursively and include them under docs['py_files'] (relative path -> content)
    py_files: Dict[str, str] = {}
    for p in base.rglob('*.py'):
        try:
            rel = p.relative_to(base).as_posix()
            py_files[rel] = p.read_text(encoding='utf-8')
        except Exception:
            continue
    if py_files:
        docs['py_files'] = py_files
    # Optional CONFIG_DOC.json
    docs_path = base / 'CONFIG_DOC.json'
    if docs_path.is_file():
        try:
            d = json.loads(docs_path.read_text(encoding='utf-8'))
            if isinstance(d, dict):
                docs.update(d)
        except Exception:
            pass
    return metadata, docs


def set_key_file(worker_name: str, key_path: str, value: Any, remove_flag: bool) -> bool:
    cfg = read_config_json(worker_name)
    if remove_flag:
        cfg = del_by_path(cfg, key_path)
    else:
        cfg = set_by_path(cfg, key_path, value)
    return write_config_json(worker_name, cfg)
