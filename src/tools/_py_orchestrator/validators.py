from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PY_WORKERS_DIR = PROJECT_ROOT / 'workers'


def validate_worker_name(worker_name: str) -> str:
    name = (worker_name or '').strip()
    if not name:
        raise ValueError("worker_name required")
    if not all(c.isalnum() or c in '-_' for c in name):
        raise ValueError("worker_name must be alphanumeric with - or _")
    return name


def _is_under(root: Path, full: Path) -> bool:
    try:
        full.relative_to(root)
        return True
    except ValueError:
        return False


def validate_params(params: dict) -> dict:
    p = dict(params or {})
    if 'operation' not in p:
        p['operation'] = 'start'
    op = p['operation']
    # Allow graph and validate operations
    if op not in {'start','stop','status','debug','list','graph','validate'}:
        raise ValueError(f"Invalid operation: {op}")

    if op != 'list':
        p['worker_name'] = validate_worker_name(p.get('worker_name'))

    if op == 'start':
        worker_file = (p.get('worker_file') or '').strip()
        if not worker_file:
            raise ValueError("worker_file required for start operation")
        # Enforce chroot under workers/
        if not (worker_file.startswith('workers/') or worker_file.startswith('./workers/')):
            raise ValueError("worker_file must be under workers/ directory")
        if '..' in worker_file or os.path.isabs(worker_file):
            raise ValueError("worker_file cannot contain .. or be absolute")
        full_path = (PROJECT_ROOT / worker_file).resolve()
        if not _is_under(PY_WORKERS_DIR, full_path):
            raise ValueError("worker_file escapes workers/ directory (symlink?)")
        if not full_path.is_file():
            raise ValueError(f"worker_file not found: {worker_file}")
        p['worker_file'] = worker_file
        p['worker_file_resolved'] = str(full_path)
    if op == 'stop':
        mode = p.get('stop', {}).get('mode', 'soft')
        if mode not in {'soft','term','kill'}:
            raise ValueError(f"Invalid stop mode: {mode}")
        if 'stop' not in p:
            p['stop'] = {}
        p['stop']['mode'] = mode
    # graph/status/debug/list/validate use their own inner validation downstream
    return p
