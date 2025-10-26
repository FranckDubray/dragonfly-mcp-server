from typing import Any

SAFE_BUILTINS = {
    'len': len,
    'range': range,
    'min': min,
    'max': max,
    'sum': sum,
    'any': any,
    'all': all,
    'enumerate': enumerate,
    'str': str,
    'int': int,
    'float': float,
    'bool': bool,
    'dict': dict,
    'list': list,
    'set': set,
    'tuple': tuple,
}


def call_step_sandboxed(fn, worker_ctx: dict, cycle: dict, env: Any):
    globs = getattr(fn, '__globals__', None)
    saved_builtins = None
    try:
        if isinstance(globs, dict):
            saved_builtins = globs.get('__builtins__')
            globs['__builtins__'] = SAFE_BUILTINS
        return fn(worker_ctx, cycle, env)
    finally:
        try:
            if isinstance(globs, dict):
                globs['__builtins__'] = saved_builtins
        except Exception:
            pass
