from __future__ import annotations
from typing import Any, Dict, List
from ..services import obs_client


def get_list(args: Dict[str, Any]) -> Dict[str, Any]:
    """Retourne la liste des transitions disponibles.
    Compat v5.x: certaines versions exposent GetSceneTransitionList, d'autres GetTransitionKindList.
    """
    # Tentative 1: GetSceneTransitionList (retourne un tableau d'objets avec transitionName)
    r = obs_client.call("GetSceneTransitionList")
    if r.get("ok"):
        lst: List[str] = [t.get("transitionName") for t in (r.get("data", {}).get("transitions", []) or [])]
        return {
            "ok": True,
            "current": None,
            "transitions": lst,
            "total_count": len(lst),
            "returned_count": len(lst),
            "truncated": False
        }
    # Tentative 2: GetTransitionKindList (retourne un tableau de strings transitionKinds)
    r2 = obs_client.call("GetTransitionKindList")
    if r2.get("ok"):
        kinds = r2.get("data", {}).get("transitionKinds", []) or []
        lst = [str(k) for k in kinds]
        return {
            "ok": True,
            "current": None,
            "transitions": lst,
            "total_count": len(lst),
            "returned_count": len(lst),
            "truncated": False
        }
    # Échec
    return r if r.get("ok") is False else r2


def get_current(args: Dict[str, Any]) -> Dict[str, Any]:
    r = obs_client.call("GetCurrentSceneTransition")
    if not r.get("ok"):
        return r
    return {"ok": True, "current": r.get("data", {}).get("transitionName")}


def get_duration(args: Dict[str, Any]) -> Dict[str, Any]:
    """Retourne la durée de la transition active si disponible.
    Compat: si GetCurrentSceneTransitionDuration indisponible, renvoie duration_ms=None.
    """
    r = obs_client.call("GetCurrentSceneTransitionDuration")
    if r.get("ok"):
        return {"ok": True, "duration_ms": r.get("data", {}).get("transitionDuration")}
    # Fallback: non disponible dans cette version → retourner None plutôt qu'une erreur dure
    return {"ok": True, "duration_ms": None}


def set_duration(args: Dict[str, Any]) -> Dict[str, Any]:
    dur = args.get("duration_ms")
    if not isinstance(dur, int) or dur < 0:
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("SetCurrentSceneTransitionDuration", {"transitionDuration": dur})
    return r if not r.get("ok") else {"ok": True, "duration_ms": dur}


def set_current(args: Dict[str, Any]) -> Dict[str, Any]:
    name = args.get("transition_name")
    if not isinstance(name, str) or not name:
        return {"ok": False, "error": "invalid_argument"}
    r = obs_client.call("SetCurrentSceneTransition", {"transitionName": name})
    return r if not r.get("ok") else {"ok": True, "current": name}
