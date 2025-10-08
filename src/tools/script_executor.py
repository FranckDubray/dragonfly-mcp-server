"""
Script Executor Tool - Execute multi-tool scripts with orchestration
SECURITY: Sandboxed execution with strict limitations

Enhancements:
- store: persist a script by name under <project_root>/script_executor
- run_named: execute a stored script by its name (avoids copy/paste from LLM memory)
- list: list stored scripts
- get: fetch stored script content
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import traceback

_SPEC_DIR = Path(__file__).resolve().parent.parent / "tool_specs"

# lightweight storage helpers (kept separate for clarity / small files)
try:
    from ._script_executor.storage import save_script, load_script, list_scripts
except Exception:  # pragma: no cover
    save_script = load_script = list_scripts = None  # type: ignore


def _load_spec_override(name: str) -> Dict[str, Any] | None:
    try:
        p = _SPEC_DIR / f"{name}.json"
        if p.is_file():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def _safe_parameters(obj: Any) -> Dict[str, Any] | None:
    # tools.function.parameters doit être un objet (ou bool). Jamais un tableau.
    return obj if isinstance(obj, dict) else None


def _make_executor(timeout: Optional[int], allowed_tools: Optional[List[str]]):
    """Create ScriptExecutor with compatibility for older versions (no allowed_tools).
    Do not force default timeout here; let underlying executor apply its own cascade.
    """
    from ._script.executor import ScriptExecutor  # type: ignore
    try:
        return ScriptExecutor(allowed_tools=allowed_tools, default_timeout=timeout)
    except TypeError:
        # Older executor without allowed_tools
        exec_inst = ScriptExecutor(default_timeout=timeout)
        if allowed_tools:
            return exec_inst, (
                "Compatibilité: la version de ScriptExecutor ne supporte pas 'allowed_tools'; "
                "la liste blanche ne sera pas appliquée. Mettez à jour src/tools/_script/executor.py."
            )
        return exec_inst, None


def _run_inline(script: str, variables: Dict[str, Any] | None, timeout: Optional[int], allowed_tools: Optional[List[str]]):
    try:
        # Create executor (handle compatibility)
        try:
            executor = _make_executor(timeout, allowed_tools)  # may return instance or (instance, warning)
            compat_warning = None
            if isinstance(executor, tuple):
                executor, compat_warning = executor
        except Exception as e:
            return {
                "success": False,
                "error": "Script executor indisponible (module _script manquant ou invalide).",
                "details": str(e),
                "hint": "Assurez-vous que src/tools/_script/* est présent et importable.",
            }

        exec_result = executor.run(script=script, variables=variables or {})

        if not isinstance(exec_result, dict):
            return {
                "success": False,
                "error": "Réponse inattendue de l'exécuteur",
                "debug": {"raw": str(exec_result)},
            }

        if not exec_result.get("success", True):
            out: Dict[str, Any] = {
                "success": False,
                "error": exec_result.get("error") or "Échec d'exécution du script",
                "help": exec_result.get("help"),
                "output": exec_result.get("output"),
                "traceback": exec_result.get("traceback"),
                "tool_calls_made": exec_result.get("tool_calls_made"),
                "available_tools": exec_result.get("available_tools"),
                "execution_time_seconds": exec_result.get("execution_time_seconds"),
            }
            if compat_warning:
                out["warning"] = compat_warning
            return out

        out: Dict[str, Any] = {
            "success": True,
            "result": exec_result.get("result"),
        }
        if exec_result.get("output") is not None:
            out["output"] = exec_result.get("output")
        if exec_result.get("available_tools") is not None:
            out["available_tools"] = exec_result.get("available_tools")
        if exec_result.get("tool_calls_made") is not None:
            out["tool_calls_made"] = exec_result.get("tool_calls_made")
        if exec_result.get("execution_time_seconds") is not None:
            out["execution_time_seconds"] = exec_result.get("execution_time_seconds")
        return out

    except Exception as e:  # pragma: no cover
        return {
            "success": False,
            "error": f"Échec d'exécution du script (wrapper): {e}",
            "exception_type": type(e).__name__,
            "traceback": traceback.format_exc(),
        }


# ---------------------------- Public tool API -----------------------------

def run(
    script: Optional[str] = None,
    variables: Dict[str, Any] | None = None,
    timeout: Optional[int] = None,
    allowed_tools: Optional[List[str]] = None,
    operation: Optional[str] = None,
    name: Optional[str] = None,
    content: Optional[str] = None,
    overwrite: Optional[bool] = None,
    **_: Any,
) -> Dict[str, Any]:
    """Execute or manage scripts.

    Operations:
      - run (default): execute inline 'script'
      - store: persist script content under script_executor/<name>.py (requires 'name' and 'content')
      - run_named: execute stored script by 'name' (variables/timeout/allowed_tools also apply)
      - list: list stored scripts
      - get: return stored script content by 'name'
    """
    op = (operation or ("run" if script else None))

    if op is None:
        return {
            "success": False,
            "error": "Paramètres insuffisants. Spécifiez 'script' (pour run) ou 'operation' parmi: run, store, run_named, list, get.",
            "help": {
                "run": ["script", "variables?", "timeout?", "allowed_tools?"],
                "store": ["name", "content", "overwrite?"],
                "run_named": ["name", "variables?", "timeout?", "allowed_tools?"],
                "list": [],
                "get": ["name"],
            },
        }

    if op == "run":
        if not script:
            return {"success": False, "error": "'script' est requis pour operation=run"}
        return _run_inline(script, variables, timeout, allowed_tools)

    if op == "store":
        if save_script is None:
            return {"success": False, "error": "Stockage indisponible"}
        if not name or not (content or script):
            return {"success": False, "error": "'name' et 'content' (ou 'script') sont requis pour store"}
        try:
            return save_script(name=name, content=(content or script), overwrite=bool(overwrite))
        except Exception as e:
            return {"success": False, "error": str(e)}

    if op == "run_named":
        if load_script is None:
            return {"success": False, "error": "Stockage indisponible"}
        if not name:
            return {"success": False, "error": "'name' est requis pour run_named"}
        try:
            loaded = load_script(name)
            if not loaded.get("success"):
                return loaded
            return _run_inline(loaded.get("content", ""), variables, timeout, allowed_tools)
        except Exception as e:
            return {"success": False, "error": str(e)}

    if op == "list":
        if list_scripts is None:
            return {"success": False, "error": "Stockage indisponible"}
        try:
            return list_scripts()
        except Exception as e:
            return {"success": False, "error": str(e)}

    if op == "get":
        if load_script is None:
            return {"success": False, "error": "Stockage indisponible"}
        if not name:
            return {"success": False, "error": "'name' est requis pour get"}
        try:
            return load_script(name)
        except Exception as e:
            return {"success": False, "error": str(e)}

    return {"success": False, "error": f"operation inconnue: {op}"}


def spec() -> Dict[str, Any]:
    base = {
        "type": "function",
        "function": {
            "name": "script_executor",
            "displayName": "Script Executor",
            "description": "Exécute des scripts Python orchestrant des outils MCP dans un bac à sable; inclut stockage minimal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["run", "store", "run_named", "list", "get"],
                        "description": "Action: run (par défaut), store, run_named, list, get"
                    },
                    "script": {
                        "type": "string",
                        "description": "Script Python (pour operation=run ou contenu si store)"
                    },
                    "variables": {
                        "type": "object",
                        "description": "Variables optionnelles injectées.",
                        "additionalProperties": True
                    },
                    "timeout": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 300,
                        "description": "Timeout en secondes (défaut: dépend de l'exécuteur)."
                    },
                    "allowed_tools": {
                        "type": "array",
                        "description": "Liste blanche des outils autorisés.",
                        "items": {"type": "string"}
                    },
                    "name": {"type": "string", "description": "Nom du script (store/run_named/get)"},
                    "content": {"type": "string", "description": "Contenu du script (store)"},
                    "overwrite": {"type": "boolean", "description": "Écraser si le fichier existe (store)"}
                },
                "required": [],
                "additionalProperties": False
            }
        }
    }

    override = _load_spec_override("script_executor")
    if isinstance(override, dict):
        ofn = override.get("function", {})
        fn = base.get("function", {})
        if isinstance(ofn.get("displayName"), str):
            fn["displayName"] = ofn["displayName"]
        if isinstance(ofn.get("description"), str):
            fn["description"] = ofn["description"]
        params = _safe_parameters(ofn.get("parameters"))
        if params:
            fn["parameters"] = params
    return base
