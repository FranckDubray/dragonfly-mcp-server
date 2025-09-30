"""
Script Executor Tool - Execute multi-tool scripts with orchestration
SECURITY: Sandboxed execution with strict limitations
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import json

_SPEC_DIR = Path(__file__).resolve().parent.parent / "tool_specs"


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


def run(
    script: str,
    variables: Dict[str, Any] | None = None,
    timeout: Optional[int] = None,
    allowed_tools: Optional[List[str]] = None,
) -> Dict[str, Any]:
    if not script:
        return {
            "success": False,
            "error": "❌ 'script' est requis",
            "help": "Fournissez un script Python qui utilise call_tool('nom', params) ou tools.nom(params=...)."
        }

    # Tente d’utiliser l’exécuteur sandbox si disponible
    try:
        from ._script.executor import ScriptExecutor  # type: ignore
    except Exception as e:
        return {
            "success": False,
            "error": "Script executor indisponible (module _script manquant).",
            "details": str(e),
            "hint": "Assurez-vous que src/tools/_script/* est présent et importable."
        }

    # Crée l'executor avec compatibilité ascendante (anciennes signatures sans allowed_tools)
    compat_warning: Optional[str] = None
    try:
        executor = ScriptExecutor(
            allowed_tools=allowed_tools,          # None -> politique par défaut interne
            default_timeout=timeout or 60,
        )
    except TypeError as te:
        # Ancienne version de ScriptExecutor ne supporte pas allowed_tools
        executor = ScriptExecutor(
            default_timeout=timeout or 60,
        )
        if allowed_tools:
            compat_warning = (
                "Compatibilité: la version de ScriptExecutor ne supporte pas 'allowed_tools'; "
                "la liste blanche ne sera pas appliquée. Mettez à jour src/tools/_script/executor.py."
            )

    try:
        exec_result = executor.run(script=script, variables=variables or {})
        # Normalise le retour
        out: Dict[str, Any] = {"success": True, "result": exec_result.get("result")}
        if "prints" in exec_result:
            out["prints"] = exec_result["prints"]
        if "tool_calls" in exec_result:
            out["tool_calls"] = exec_result["tool_calls"]
        if "stats" in exec_result:
            out["stats"] = exec_result["stats"]
        if "usage" in exec_result:
            out["usage"] = exec_result["usage"]
        if exec_result.get("output") is not None:
            out["output"] = exec_result.get("output")
        if exec_result.get("available_tools") is not None:
            out["available_tools"] = exec_result.get("available_tools")
        if exec_result.get("tool_calls_made") is not None:
            out["tool_calls_made"] = exec_result.get("tool_calls_made")
        if exec_result.get("execution_time_seconds") is not None:
            out["execution_time_seconds"] = exec_result.get("execution_time_seconds")
        if compat_warning:
            out["warning"] = compat_warning
        return out
    except Exception as e:
        return {
            "success": False,
            "error": f"Echec d'exécution du script: {e}"
        }


def spec() -> Dict[str, Any]:
    base = {
        "type": "function",
        "function": {
            "name": "script_executor",
            "displayName": "Script Executor",
            "description": "Exécute des scripts Python orchestrant des outils MCP dans un bac à sable.",
            "parameters": {
                "type": "object",
                "properties": {
                    "script": {
                        "type": "string",
                        "description": "Script Python orchestrant des appels MCP via call_tool() ou tools.<nom>()."
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
                        "description": "Timeout en secondes (défaut: 60)."
                    },
                    "allowed_tools": {
                        "type": "array",
                        "description": "Liste blanche des outils autorisés.",
                        "items": {"type": "string"}
                    }
                },
                "required": ["script"],
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
