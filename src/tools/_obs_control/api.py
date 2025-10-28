"""
Dispatcher unique pour le tool obs_control (léger, <7KB).
- Valide le top-level puis dispatch via une table de routage (registry).
- Gère les sessions utilitaires, le batch et le raw request.
- Try/catch global pour erreurs propres.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .validators import validate_top_level
from .services.session_mgr import close_session, open_session
from .registry import get_routes
from .services import sequencer


ROUTES = get_routes()


def _exec_single(action: str, args: Dict[str, Any], wait: bool, timeout_sec: int | None, session_id: str | None, dry_run: bool) -> Dict[str, Any]:
    handler = ROUTES.get(action)
    if not handler:
        return {"ok": False, "error": "action_not_implemented", "message": f"Action '{action}' non implémentée"}
    return handler(args, wait, timeout_sec, session_id, dry_run)


def run(**params: Any) -> Dict[str, Any]:
    try:
        action, args, wait, timeout_sec, session_id, dry_run = validate_top_level(params)

        # Sessions utilitaires
        if action == "session_open":
            tout = args.get("session_timeout_sec") if isinstance(args, dict) else None
            note = args.get("note") if isinstance(args, dict) else None
            return open_session(session_timeout_sec=tout, note=note) | {"ok": True}
        if action == "session_close":
            sid = args.get("session_id") if isinstance(args, dict) else None
            if not isinstance(sid, str) or not sid:
                return {"ok": False, "error": "invalid_argument", "message": "session_id requis"}
            res = close_session(sid)
            return {"ok": True, **res}
        if action == "batch_execute":
            acts: List[Dict[str, Any]] = args.get("actions") if isinstance(args, dict) else None
            if not isinstance(acts, list):
                return {"ok": False, "error": "invalid_argument", "message": "actions doit être une liste"}
            results: List[Dict[str, Any]] = []
            for item in acts:
                if not isinstance(item, dict):
                    results.append({"ok": False, "error": "invalid_argument"})
                    continue
                a = item.get("action") or item.get("name")
                a_args = item.get("args") or item.get("params") or {}
                res = _exec_single(a, a_args, wait, timeout_sec, session_id, dry_run) if isinstance(a, str) else {"ok": False, "error": "invalid_argument"}
                results.append(res)
            return {"ok": True, "results": results}

        # Nouveau: séquenceur
        if action == "sequence_schedule":
            steps = args.get("steps") if isinstance(args, dict) else None
            note = args.get("note") if isinstance(args, dict) else None
            if not isinstance(steps, list) or not steps:
                return {"ok": False, "error": "invalid_argument", "message": "steps requis (liste non vide)"}
            return sequencer.schedule(steps, note=note)
        if action == "sequence_cancel":
            sid = args.get("script_id") if isinstance(args, dict) else None
            if not isinstance(sid, str) or not sid:
                return {"ok": False, "error": "invalid_argument", "message": "script_id requis"}
            return sequencer.cancel(sid)
        if action == "sequence_status":
            sid = args.get("script_id") if isinstance(args, dict) else None
            if not isinstance(sid, str) or not sid:
                return {"ok": False, "error": "invalid_argument", "message": "script_id requis"}
            return sequencer.get_status(sid)

        # Dispatch unique
        return _exec_single(action, args, wait, timeout_sec, session_id, dry_run)

    except Exception as e:
        return {"ok": False, "error": "unexpected_error", "message": f"obs_control: erreur inattendue: {type(e).__name__}"}
