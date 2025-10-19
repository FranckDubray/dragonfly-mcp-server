# Handlers registry bootstrap (IO + transforms)
from .base import AbstractHandler, HandlerError
from .registry import HandlerRegistry, get_registry
from .http_tool import HttpToolHandler
from .sleep import SleepHandler

# Dynamic import of transforms packages (one file per transform)
import pkgutil, importlib, pathlib, os

__all__ = [
    'AbstractHandler', 'HandlerError', 'HandlerRegistry', 'get_registry',
    'HttpToolHandler', 'SleepHandler'
]


def bootstrap_handlers(cancel_flag_fn=None):
    registry = get_registry()

    # IO handlers
    if not registry.has('http_tool'):
        registry.register(HttpToolHandler())
    if cancel_flag_fn and not registry.has('sleep'):
        registry.register(SleepHandler(cancel_flag_fn))

    # Load transforms from packages
    base_dir = pathlib.Path(__file__).resolve().parent
    for pkg_name in ['transforms', 'transforms_domain']:
        pkg_path = base_dir / pkg_name
        if not pkg_path.is_dir():
            continue
        for _, modname, ispkg in pkgutil.iter_modules([str(pkg_path)]):
            if ispkg:
                continue
            module = importlib.import_module(f"{__package__}.{pkg_name}.{modname}")
            # Register any class with 'kind' property and 'run' method
            for attr in dir(module):
                obj = getattr(module, attr)
                if isinstance(obj, type) and hasattr(obj, 'kind') and callable(getattr(obj, 'run', None)):
                    try:
                        inst = obj()
                        if not registry.has(inst.kind):
                            registry.register(inst)
                    except Exception:
                        pass
