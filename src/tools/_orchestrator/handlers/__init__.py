

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

    # Explicit import to ensure specific handlers are importable even if scan misses files
    try:
        from .transforms_domain.coerce_number import CoerceNumberHandler  # noqa: F401
        from .transforms_domain.normalize_entities import NormalizeEntitiesHandler  # noqa: F401
        from .transforms_domain.pos_to_square import PosToSquareHandler  # noqa: F401
        from .transforms_domain.compare_positions import ComparePositionsHandler  # noqa: F401
        from .transforms_domain.uci_build import UciBuildHandler  # noqa: F401
        from .transforms_domain.uci_parse import UciParseHandler  # noqa: F401
        from .transforms_domain.board_coords import BoardCoordsHandler  # noqa: F401
        from .transforms_domain.template_map import TemplateMapHandler  # noqa: F401
        from .transforms_domain.array_concat import ArrayConcatHandler  # noqa: F401
    except Exception:
        pass

    # Explicit registration for critical transforms (in case dynamic scan missed them)
    try:
        from .transforms_domain.coerce_number import CoerceNumberHandler
        from .transforms_domain.normalize_entities import NormalizeEntitiesHandler
        from .transforms_domain.pos_to_square import PosToSquareHandler
        from .transforms_domain.compare_positions import ComparePositionsHandler
        from .transforms_domain.uci_build import UciBuildHandler
        from .transforms_domain.uci_parse import UciParseHandler
        from .transforms_domain.board_coords import BoardCoordsHandler
        from .transforms_domain.template_map import TemplateMapHandler
        from .transforms_domain.array_concat import ArrayConcatHandler
        for cls in (
            BoardCoordsHandler,
            TemplateMapHandler,
            NormalizeEntitiesHandler,
            PosToSquareHandler,
            ComparePositionsHandler,
            UciBuildHandler,
            UciParseHandler,
            CoerceNumberHandler,
            ArrayConcatHandler,
        ):
            try:
                inst = cls()
                if not registry.has(inst.kind):
                    registry.register(inst)
            except Exception as e:
                print(f"[orchestrator.handlers] failed to register {getattr(cls,'__name__','?')}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"[orchestrator.handlers] warning: explicit import/register block failed: {e}", file=sys.stderr)
