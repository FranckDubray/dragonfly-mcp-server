












# Input validation for orchestrator tool (spec-aligned)
# Chroot enforcement: workers/ only, no .., no absolute paths, no escaping symlinks

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]  # dragonfly-mcp-server/
WORKERS_DIR = PROJECT_ROOT / 'workers'

def validate_worker_name(worker_name: str) -> str:
    """Validate worker_name (alnum, -, _) and return normalized value.
    Raises ValueError if invalid.
    """
    name = (worker_name or '').strip()
    if not name:
        raise ValueError("worker_name required")
    if not all(c.isalnum() or c in '-_' for c in name):
        raise ValueError("worker_name must be alphanumeric with - or _")
    return name


def validate_params(params: dict) -> dict:
    """Validate and normalize params (raises ValueError if invalid)"""
    p = dict(params or {})
    
    # Default operation
    if 'operation' not in p:
        p['operation'] = 'start'
    
    op = p['operation']
    if op not in {'start', 'stop', 'status', 'debug', 'list'}:
        raise ValueError(f"Invalid operation: {op}")
    
    # worker_name required for all operations except 'list'
    if op != 'list':
        p['worker_name'] = validate_worker_name(p.get('worker_name'))
    
    # Start operation: worker_file required and chrooted
    if op == 'start':
        worker_file = (p.get('worker_file') or '').strip()
        if not worker_file:
            raise ValueError("worker_file required for start operation")
        
        # Enforce chroot under workers/
        if not worker_file.startswith('workers/'):
            raise ValueError("worker_file must be under workers/ directory")
        
        # Reject .. and absolute paths
        if '..' in worker_file or os.path.isabs(worker_file):
            raise ValueError("worker_file cannot contain .. or be absolute")
        
        # Resolve full path and verify it stays inside workers/
        full_path = (PROJECT_ROOT / worker_file).resolve()
        try:
            full_path.relative_to(WORKERS_DIR)
        except ValueError:
            raise ValueError("worker_file escapes workers/ directory (symlink?)")
        
        # Check file exists and readable
        if not full_path.is_file():
            raise ValueError(f"worker_file not found: {worker_file}")
        
        p['worker_file'] = worker_file
        p['worker_file_resolved'] = str(full_path)
    
    # Stop operation: mode validation
    if op == 'stop':
        mode = p.get('stop', {}).get('mode', 'soft')
        if mode not in {'soft', 'term', 'kill'}:
            raise ValueError(f"Invalid stop mode: {mode}")
        if 'stop' not in p:
            p['stop'] = {}
        p['stop']['mode'] = mode
    
    return p
