
from __future__ import annotations
from typing import Dict, Any
from pathlib import Path
import json as _json
from ..db import set_state_kv


def _deep_update(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in (src or {}).items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _deep_update(dst[k], v)
        else:
            dst[k] = v
    return dst


def merge_worker_config(root: Path, process: Any, db_path: str, worker: str) -> bool:
    """Merge config/ into process.metadata and persist KV.
    - config/config.json → deep-merge into metadata
    - config/prompts/*.md|*.txt → metadata.prompts[stem] = content
    - config/CONFIG_DOC.json (optional) → KV docs
    Returns True if any metadata was merged.
    """
    try:
        cfg_dir = root / 'config'
        merged_any = False
        docs = None
        if not isinstance(getattr(process, 'metadata', None), dict):
            process.metadata = {}
        # config.json
        json_path = cfg_dir / 'config.json'
        if json_path.is_file():
            try:
                add = _json.loads(json_path.read_text(encoding='utf-8'))
                if isinstance(add, dict):
                    _deep_update(process.metadata, add)
                    merged_any = True
            except Exception:
                pass
        # prompts
        prompts_dir = cfg_dir / 'prompts'
        if prompts_dir.is_dir():
            for p in sorted(prompts_dir.glob('*')):
                if p.suffix.lower() in {'.md', '.txt'} and p.is_file():
                    try:
                        txt = p.read_text(encoding='utf-8')
                    except Exception:
                        txt = ''
                    if 'prompts' not in process.metadata or not isinstance(process.metadata.get('prompts'), dict):
                        process.metadata['prompts'] = {}
                    process.metadata['prompts'][p.stem] = txt
                    merged_any = True
        # CONFIG_DOC.json (optional)
        docs_path = cfg_dir / 'CONFIG_DOC.json'
        if docs_path.is_file():
            try:
                docs = _json.loads(docs_path.read_text(encoding='utf-8'))
            except Exception:
                docs = None
        # Persist KV
        try:
            set_state_kv(db_path, worker, 'py.process_metadata', _json.dumps(process.metadata or {}))
        except Exception:
            pass
        if isinstance(docs, dict):
            try:
                set_state_kv(db_path, worker, 'py.process_config_docs', _json.dumps(docs))
            except Exception:
                pass
        return merged_any
    except Exception:
        return False
