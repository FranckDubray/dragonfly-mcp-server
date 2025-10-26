# Handlers registry bootstrap (IO + transforms) — Python Orchestrator AUTONOME
from .base import AbstractHandler, HandlerError
from .registry import HandlerRegistry, get_registry

import pkgutil, importlib, pathlib, sys, inspect, json

__all__ = [
    'AbstractHandler', 'HandlerError', 'HandlerRegistry', 'get_registry'
]

def bootstrap_handlers(cancel_flag_fn=None):
    registry = get_registry()

    # Sleep handler (si présent localement)
    try:
        if cancel_flag_fn and not registry.has('sleep'):
            from .sleep import SleepHandler
            registry.register(SleepHandler(cancel_flag_fn))
    except Exception:
        pass

    # Chargement “dynamique”: découverte des modules déclarant des handlers
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
                # Auto-enregistrer les classes concrètes qui héritent d'AbstractHandler
                for attr in dir(module):
                    obj = getattr(module, attr)
                    if (
                        isinstance(obj, type)
                        and issubclass(obj, AbstractHandler)
                        and obj is not AbstractHandler
                        and getattr(obj, '__module__', '') == module.__name__
                        and callable(getattr(obj, 'run', None))
                    ):
                        try:
                            inst = obj()
                            if not registry.has(inst.kind):
                                registry.register(inst)
                        except Exception as reg_e:
                            print(f"[py_orch.handlers] fail register '{attr}' from {pkg_name}/{modname}: {reg_e}", file=sys.stderr)
            except Exception as imp_e:
                print(f"[py_orch.handlers] fail import module {pkg_name}/{modname}: {imp_e}", file=sys.stderr)

    # Fallback explicite: quelques handlers critiques
    try:
        from .transforms_domain.sanitize_text import SanitizeTextHandler
        from .transforms_domain.template_map import TemplateMapHandler
        from .transforms_domain.array_concat import ArrayConcatHandler
        from .transforms_domain.coerce_number import CoerceNumberHandler
        from .transforms_domain.normalize_entities import NormalizeEntitiesHandler
        from .transforms_domain.pos_to_square import PosToSquareHandler
        from .transforms_domain.compare_positions import ComparePositionsHandler
        from .transforms_domain.uci_build import UciBuildHandler
        from .transforms_domain.uci_parse import UciParseHandler
        from .transforms_domain.board_coords import BoardCoordsHandler
        # Normalisation LLM (critique pour curation v2)
        NLOH = None
        try:
            from .transforms_domain.normalize_llm_output import NormalizeLlmOutputHandler as NLOH
        except Exception:
            try:
                from .transforms_domain.normalize_llm_output import NormalizeLLMOutputHandler as NLOH
            except Exception:
                NLOH = None
        critical = [
            SanitizeTextHandler,
            TemplateMapHandler,
            ArrayConcatHandler,
            CoerceNumberHandler,
            NormalizeEntitiesHandler,
            PosToSquareHandler,
            ComparePositionsHandler,
            UciBuildHandler,
            UciParseHandler,
            BoardCoordsHandler,
        ]
        if NLOH:
            critical.append(NLOH)
        for cls in critical:
            try:
                inst = cls()
                if not registry.has(inst.kind):
                    registry.register(inst)
            except Exception as e:
                print(f"[py_orch.handlers] explicit register {getattr(cls,'__name__','?')} failed: {e}", file=sys.stderr)
        # Si normalize_llm_output reste introuvable, enregistrer un shim minimal
        try:
            if not registry.has('normalize_llm_output'):
                class _NormalizeLlmOutputShim(AbstractHandler):
                    @property
                    def kind(self) -> str:
                        return 'normalize_llm_output'
                    def run(self, content=None, fallback_value=None, **kwargs):
                        # Minimal: si dict/list → parsed = content; si str→json.loads; sinon fallback ([])
                        parsed = []
                        if isinstance(content, (list, dict)):
                            parsed = content
                        elif isinstance(content, str):
                            try:
                                parsed = json.loads(content)
                            except Exception:
                                parsed = fallback_value if fallback_value is not None else []
                        else:
                            parsed = fallback_value if fallback_value is not None else []
                        return {'parsed': parsed}
                registry.register(_NormalizeLlmOutputShim())
        except Exception as e:
            print(f"[py_orch.handlers] warning: could not register shim normalize_llm_output: {e}", file=sys.stderr)
    except Exception as e:
        print(f"[py_orch.handlers] warning: explicit import block failed: {e}", file=sys.stderr)
