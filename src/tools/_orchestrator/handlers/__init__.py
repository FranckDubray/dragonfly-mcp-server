
# Handlers registry bootstrap (IO + transforms)
from .base import AbstractHandler, HandlerError
from .registry import HandlerRegistry, get_registry
from .http_tool import HttpToolHandler
from .sleep import SleepHandler

# Dynamic import of transforms packages (one file per transform)
import pkgutil, importlib, pathlib, os, sys, inspect

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
            try:
                module = importlib.import_module(f"{__package__}.{pkg_name}.{modname}")
                # Register any concrete handler class defined in this module
                for attr in dir(module):
                    obj = getattr(module, attr)
                    if (
                        isinstance(obj, type)
                        and issubclass(obj, AbstractHandler)
                        and obj is not AbstractHandler
                        and not inspect.isabstract(obj)
                        and getattr(obj, '__module__', '') == module.__name__
                        and callable(getattr(obj, 'run', None))
                    ):
                        try:
                            inst = obj()
                            if not registry.has(inst.kind):
                                registry.register(inst)
                        except Exception as reg_e:
                            print(
                                f"[orchestrator.handlers] failed to register handler '{attr}' from {pkg_name}/{modname}: {reg_e}",
                                file=sys.stderr,
                            )
            except Exception as imp_e:
                print(
                    f"[orchestrator.handlers] failed to import module {pkg_name}/{modname}: {imp_e}",
                    file=sys.stderr,
                )

# Explicit import to ensure coerce_number is discoverable in transforms_domain
try:
    from .transforms_domain.coerce_number import CoerceNumberHandler  # noqa: F401
except Exception:
    pass
