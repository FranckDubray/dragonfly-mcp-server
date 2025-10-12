
from typing import Any, Dict, List, Tuple
from ._call_llm.core import execute_call_llm
import os, base64, mimetypes
from pathlib import Path

# Politique d'accès images (serveur dev):
# - Détection intelligente de la racine projet (remonte depuis src/tools/)
# - Docs est relatif à la racine projet: <projet>/docs/
# - Optionnel: DOCS_ABS_ROOT permet de surcharger la racine absolue
PROJECT_ROOT = Path(__file__).parent.parent.parent  # remonte de 3 niveaux: tools/ -> src/ -> projet/
DEFAULT_DOCS = str(PROJECT_ROOT / "docs")
DOCS_ABS_ROOT = os.getenv("DOCS_ABS_ROOT", DEFAULT_DOCS)


def _to_abs_docs(path: str) -> Tuple[str | None, Dict[str, Any]]:
    """Normalise un chemin image sous DOCS_ABS_ROOT.
    Règles:
    - Si 'path' est absolu et commence par DOCS_ABS_ROOT → on l'utilise tel quel
    - Si 'path' est relatif et commence par 'docs' → on le mappe vers DOCS_ABS_ROOT + suffixe
    - Si 'path' est relatif sans 'docs' → on l'ajoute directement sous DOCS_ABS_ROOT
    Retourne (full_abs | None, diag)
    diag: {input, resolved, docs_abs_root, is_abs, under_allowed}
    """
    diag: Dict[str, Any] = {
        "input": path,
        "docs_abs_root": DOCS_ABS_ROOT,
        "is_abs": False,
        "resolved": None,
        "under_allowed": False,
    }
    try:
        if not isinstance(path, str) or not path.strip():
            diag["reason"] = "empty_or_invalid_path"
            return None, diag
        p = os.path.normpath(path.strip())
        root = os.path.normpath(DOCS_ABS_ROOT)
        
        # Absolu sous DOCS_ABS_ROOT → accepter tel quel
        if os.path.isabs(p):
            diag["is_abs"] = True
            if p == root or p.startswith(root + os.sep):
                full_abs = p
            else:
                diag["reason"] = "abs_not_under_docs_root"
                diag["resolved"] = p
                return None, diag
        else:
            # Relatif commençant par 'docs/' → enlever le préfixe et mapper
            if p == "docs" or p.startswith("docs" + os.sep):
                suffix = p[4:].lstrip(os.sep)
                full_abs = os.path.normpath(os.path.join(root, suffix)) if suffix else root
            else:
                # Relatif sans 'docs/' → ajouter directement sous DOCS_ABS_ROOT
                full_abs = os.path.normpath(os.path.join(root, p))
        
        diag["resolved"] = full_abs
        under = (full_abs == root) or full_abs.startswith(root + os.sep)
        diag["under_allowed"] = under
        if not under:
            diag["reason"] = "not_under_allowed_root"
            return None, diag
        return full_abs, diag
    except Exception as e:
        diag["reason"] = "exception"
        diag["exception"] = str(e)
        return None, diag


def _file_to_data_url(path: str) -> Tuple[str | None, Dict[str, Any]]:
    diag: Dict[str, Any] = {"path": path}
    try:
        full_abs, diag_map = _to_abs_docs(path)
        diag.update({"map": diag_map})
        if not full_abs:
            diag["reason"] = "mapping_failed"
            return None, diag
        diag["full_abs"] = full_abs
        # Taille max
        try:
            max_bytes = int(os.getenv("LLM_MAX_IMAGE_FILE_BYTES", "5000000"))
        except Exception:
            max_bytes = 5000000
        diag["max_bytes"] = max_bytes
        exists = os.path.exists(full_abs)
        diag["exists"] = exists
        if not exists:
            diag["reason"] = "file_not_found"
            return None, diag
        try:
            size = os.path.getsize(full_abs)
        except Exception as e:
            diag["reason"] = "getsize_failed"
            diag["exception"] = str(e)
            return None, diag
        diag["size"] = size
        if size > max_bytes:
            diag["reason"] = "too_large"
            return None, diag
        try:
            with open(full_abs, "rb") as f:
                data = f.read()
        except Exception as e:
            diag["reason"] = "open_failed"
            diag["exception"] = str(e)
            return None, diag
        mime, _ = mimetypes.guess_type(full_abs)
        diag["mime_guess"] = mime or "application/octet-stream"
        if not mime:
            mime = "application/octet-stream"
        try:
            b64 = base64.b64encode(data).decode("ascii")
        except Exception as e:
            diag["reason"] = "base64_encode_failed"
            diag["exception"] = str(e)
            return None, diag
        data_url = f"data:{mime};base64,{b64}"
        diag["ok"] = True
        return data_url, diag
    except Exception as e:
        diag["reason"] = "unexpected_exception"
        diag["exception"] = str(e)
        return None, diag


def _image_part_from_url(u: str) -> Dict[str, Any]:
    # Format OpenAI robuste: image_url est un objet {url, detail?}
    return {"type": "image_url", "image_url": {"url": u}}


def run(operation: str = "run", **params) -> Dict[str, Any]:
    """Facade for call_llm tool. Requires 'model' explicitly.
    Supporte vision via 'image_urls' (http(s) ou data URL) et 'image_files' (chemins sous docs/).
    Si 'messages' est fourni, il est utilisé tel quel et image_* sont ignorés.
    """
    debug = bool(params.get("debug"))
    if not params.get("model"):
        out = {"error": "Missing required parameter: model"}
        if debug:
            out["debug"] = {"stage": "pre", "params_keys": list(params.keys())}
        return out

    messages = params.pop("messages", None)
    image_urls = params.pop("image_urls", None) or []
    image_files = params.pop("image_files", None) or []

    # Mode simple avec 'message'
    msg = params.pop("message", None)

    debug_info: Dict[str, Any] = {"images": {"files": [], "urls": []}, "docs_root": DOCS_ABS_ROOT} if debug else {}

    if not messages:
        if not msg:
            out = {"error": "Missing required parameter: message"}
            if debug:
                out["debug"] = {"stage": "pre", "hint": "message_required_when_messages_absent"}
            return out
        parts: List[Dict[str, Any]] = []
        if isinstance(msg, str) and msg.strip():
            parts.append({"type": "text", "text": msg})
        # Limites
        try:
            max_img = int(os.getenv("LLM_MAX_IMAGE_COUNT", "4"))
        except Exception:
            max_img = 4
        total_imgs = len(image_urls) + len(image_files)
        if total_imgs > max_img:
            out = {"error": f"Too many images: {total_imgs} > {max_img} (LLM_MAX_IMAGE_COUNT)."}
            if debug:
                out["debug"] = {"stage": "limit", "image_urls_count": len(image_urls), "image_files_count": len(image_files), "max_img": max_img}
            return out
        # URLs directes
        for u in image_urls:
            if isinstance(u, str) and u.strip():
                parts.append(_image_part_from_url(u))
                if debug:
                    debug_info["images"]["urls"].append({"url": u})
        # Fichiers locaux → data URL
        for p in image_files:
            if not isinstance(p, str) or not p.strip():
                if debug:
                    debug_info["images"]["files"].append({"path": p, "skipped": True, "reason": "empty_or_invalid"})
                continue
            data_url, diag = _file_to_data_url(p)
            if not data_url:
                out = {"error": f"Image file not allowed/too large/unreadable: {p}. Allowed root: {DOCS_ABS_ROOT}/"}
                if debug:
                    debug_info["images"]["files"].append({"path": p, "ok": False, "diag": diag})
                    out["debug"] = debug_info
                return out
            parts.append(_image_part_from_url(data_url))
            if debug:
                debug_info["images"]["files"].append({"path": p, "ok": True, "diag": diag})
        if not parts:
            out = {"error": "No valid content built from 'message'/'image_urls'/'image_files'."}
            if debug:
                out["debug"] = debug_info
            return out
        messages = [{"role": "user", "content": parts}]

    model = params.pop("model")
    max_tokens = params.pop("max_tokens", None)
    tool_names = params.pop("tool_names", None)
    promptSystem = params.pop("promptSystem", None)
    # debug est déjà extrait plus haut et conservé

    result = execute_call_llm(
        messages=messages,
        model=model,
        max_tokens=max_tokens,
        tool_names=tool_names,
        promptSystem=promptSystem,
        debug=debug,
    )
    # Enrichit le debug retour avec notre debug local (images)
    if debug and isinstance(result, dict):
        if "debug" in result and isinstance(result["debug"], dict):
            result["debug"].setdefault("call_llm_tool", {})
            result["debug"]["call_llm_tool"].update(debug_info)
        else:
            result["debug"] = {"call_llm_tool": debug_info}
    return result


def spec() -> Dict[str, Any]:
    # Load canonical JSON spec (source of truth)
    import json, os
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'call_llm.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)
