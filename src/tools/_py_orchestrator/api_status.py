
from .status.status_core import build_status as _build_status
from pathlib import Path
from .api_common import PROJECT_ROOT


def _relpath_from_root(p: str) -> str:
    try:
        if not p:
            return p
        abs_p = Path(p).resolve()
        root = PROJECT_ROOT.resolve()
        return abs_p.relative_to(root).as_posix()
    except Exception:
        return p


def status(params: dict) -> dict:
    out = _build_status(params)
    # Normalize paths to be relative to project root (db_path, log_path if present)
    try:
        if isinstance(out, dict):
            if 'db_path' in out:
                out['db_path'] = _relpath_from_root(out.get('db_path'))
            if 'log_path' in out:
                out['log_path'] = _relpath_from_root(out.get('log_path'))
    except Exception:
        pass
    try:
        m = out.get('metrics') or {}
        # llm_usage peut être soit top-level, soit imbriqué dans metrics
        llm = out.get('llm_usage') or (m.get('llm_usage') if isinstance(m, dict) else {}) or {}
        if isinstance(m, dict) and isinstance(llm, dict) and llm:
            # Refléter llm_usage dans metrics pour cohérence UI
            m['llm_tokens'] = {
                'total': llm.get('total_tokens', 0),
                'input': llm.get('input_tokens', 0),
                'output': llm.get('output_tokens', 0),
            }
            m['token_llm'] = llm.get('by_model') or {}
            out['metrics'] = m
    except Exception:
        pass
    return out
