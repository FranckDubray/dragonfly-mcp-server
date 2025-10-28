"""
Service client OBS v5 (simpleobsws).
- Conformité stricte simpleobsws v1.4.x: IdentificationParameters + Request objects.
- Appels de haut niveau: call(request_type, request_data) et call_batch(list[ {request_type, request_data} ]).
- Connexion éphémère par appel (one-shot). Sessions longues gérées par session_mgr si besoin.
- Aucun side-effect à l'import.
"""
from __future__ import annotations

import os
import asyncio
import threading
from typing import Any, Dict, List, Optional, Tuple

# Types simples de retour
ObsResult = Dict[str, Any]


def _get_cfg() -> Dict[str, Any]:
    return {
        "url": os.getenv("OBS_WS_URL", "ws://127.0.0.1:4455"),
        "password": os.getenv("OBS_WS_PASSWORD"),
        "connect_timeout": int(os.getenv("CONNECT_TIMEOUT_MS", "2500")),
    }


def _has_simpleobsws() -> bool:
    try:
        import simpleobsws  # type: ignore
        return True
    except Exception:
        return False


def _run_coro_in_thread(coro: asyncio.coroutines) -> Tuple[bool, Any]:
    """Exécute une coroutine dans une nouvelle boucle asyncio sur un thread séparé.
    Retourne (success, result_or_exception).
    """
    result: Any | None = None
    exc: BaseException | None = None

    def _target():
        nonlocal result, exc
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(coro)  # type: ignore
        except BaseException as e:  # noqa: BLE001
            exc = e
        finally:
            try:
                loop.close()  # type: ignore[name-defined]
            except Exception:
                pass

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join()
    if exc is not None:
        return False, exc
    return True, result


async def _connect_and_identify(ws, timeout_s: float) -> None:
    # Connexion + handshake Identify v5 (nécessaire même sans mot de passe)
    await asyncio.wait_for(ws.connect(), timeout=timeout_s)
    await asyncio.wait_for(ws.wait_until_identified(), timeout=timeout_s)


async def _call_async(request_type: str, request_data: Optional[Dict[str, Any]] = None) -> ObsResult:
    try:
        import simpleobsws  # type: ignore
    except Exception:
        return {
            "ok": False,
            "error": "dependency_missing",
            "message": "Le client OBS nécessite simpleobsws (pip install simpleobsws)."
        }

    cfg = _get_cfg()
    try:
        # IdentificationParameters requis v5; pas d'auth si password None
        ident = simpleobsws.IdentificationParameters(ignoreNonFatalRequestChecks=False)  # type: ignore[attr-defined]
        ws = simpleobsws.WebSocketClient(url=cfg["url"], password=cfg["password"], identification_parameters=ident)  # type: ignore
        await _connect_and_identify(ws, timeout_s=cfg["connect_timeout"]/1000)
        req_obj = simpleobsws.Request(request_type, request_data or {})  # type: ignore[attr-defined]
        resp = await ws.call(req_obj)
        if resp.ok():  # type: ignore[attr-defined]
            return {"ok": True, "data": resp.responseData}  # type: ignore[attr-defined]
        return {"ok": False, "error": "obs_error", "message": str(resp.requestStatus)}  # type: ignore[attr-defined]
    except asyncio.TimeoutError:
        return {"ok": False, "error": "obs_unavailable", "message": "Timeout connexion/identify OBS"}
    except Exception:
        # Pas de détails verbeux en prod
        return {"ok": False, "error": "obs_unavailable", "message": "OBS non disponible ou erreur"}
    finally:
        try:
            await ws.disconnect()
        except Exception:
            pass


def call(request_type: str, request_data: Optional[Dict[str, Any]] = None) -> ObsResult:
    """Appel one-shot synchrone, compatible avec un serveur async.
    - Si une boucle est active (FastAPI/uvicorn): exécuter la coroutine dans un thread dédié.
    - Sinon: asyncio.run directement.
    """
    if not _has_simpleobsws():
        return {
            "ok": False,
            "error": "dependency_missing",
            "message": "Le client OBS nécessite simpleobsws (pip install simpleobsws)."
        }
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        ok, res = _run_coro_in_thread(_call_async(request_type, request_data))
        if not ok:
            return {"ok": False, "error": "unexpected_error", "message": f"obs_client thread error"}
        return res  # type: ignore[return-value]
    else:
        return asyncio.run(_call_async(request_type, request_data))


async def _call_batch_async(requests: List[Dict[str, Any]]) -> ObsResult:
    try:
        import simpleobsws  # type: ignore
    except Exception:
        return {
            "ok": False,
            "error": "dependency_missing",
            "message": "Le client OBS nécessite simpleobsws (pip install simpleobsws)."
        }

    cfg = _get_cfg()
    try:
        ident = simpleobsws.IdentificationParameters(ignoreNonFatalRequestChecks=False)  # type: ignore[attr-defined]
        ws = simpleobsws.WebSocketClient(url=cfg["url"], password=cfg["password"], identification_parameters=ident)  # type: ignore
        await _connect_and_identify(ws, timeout_s=cfg["connect_timeout"]/1000)
        req_objs = [simpleobsws.Request(x.get("request_type"), x.get("request_data") or {}) for x in requests]  # type: ignore[attr-defined]
        batch = await ws.call_batch(req_objs)  # executionType par défaut (SerialRealtime)
        results = []
        for r in batch:
            if r.ok():  # type: ignore[attr-defined]
                results.append({"ok": True, "data": r.responseData})  # type: ignore[attr-defined]
            else:
                results.append({"ok": False, "error": "obs_error", "message": str(r.requestStatus)})  # type: ignore[attr-defined]
        return {"ok": True, "data": results}
    except asyncio.TimeoutError:
        return {"ok": False, "error": "obs_unavailable", "message": "Timeout connexion/identify OBS"}
    except Exception:
        return {"ok": False, "error": "obs_unavailable", "message": "OBS non disponible ou erreur"}
    finally:
        try:
            await ws.disconnect()
        except Exception:
            pass


def call_batch(requests: List[Dict[str, Any]]) -> ObsResult:
    if not _has_simpleobsws():
        return {
            "ok": False,
            "error": "dependency_missing",
            "message": "Le client OBS nécessite simpleobsws (pip install simpleobsws)."
        }
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        ok, res = _run_coro_in_thread(_call_batch_async(requests))
        if not ok:
            return {"ok": False, "error": "unexpected_error", "message": "obs_client thread error"}
        return res  # type: ignore[return-value]
    else:
        return asyncio.run(_call_batch_async(requests))
