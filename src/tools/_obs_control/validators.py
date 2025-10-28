"""
Validations pour obs_control.
- Valide les paramètres top-level et applique des valeurs par défaut.
- Vérifie que l'action demandée est supportée par la spec v1 (enum).
- Ne réalise aucune I/O ni import coûteux.
"""
from __future__ import annotations
from typing import Any, Dict, Tuple

# Enum des actions supportées (doit refléter la spec JSON canonique)
ALLOWED_ACTIONS = {
    "session_open","session_close","batch_execute","raw_request","get_version",
    "status_snapshot",
    "scenes_list","scenes_set_current","scenes_set_preview","scenes_transition_to_program","scenes_create","scenes_delete","scenes_rename","scenes_set_default_transition","scene_transition_override_get","scene_transition_override_set",
    "scene_items_list","scene_items_set_enabled","scene_items_set_transform","scene_items_set_order","scene_items_add","scene_items_remove","scene_item_set_locked",
    "inputs_list","inputs_kind_list","inputs_create","inputs_remove","inputs_rename","inputs_get_settings","inputs_set_settings","inputs_set_mute","inputs_set_volume","inputs_set_monitor_type","inputs_press_button",
    "media_status","media_action","media_seek",
    "audio_balance_set","audio_sync_offset_set",
    "filters_list","filters_add","filters_remove","filters_rename","filters_set_enabled","filters_set_settings",
    "transitions_get_list","transitions_get_current","transitions_get_duration","transitions_set_duration","transitions_set_current",
    "outputs_stream_start","outputs_stream_stop","outputs_stream_status",
    "outputs_record_start","outputs_record_stop","outputs_record_pause","outputs_record_resume","outputs_record_status",
    "outputs_replay_start","outputs_replay_stop","outputs_replay_save","outputs_replay_status",
    "outputs_virtualcam_start","outputs_virtualcam_stop","outputs_virtualcam_status",
    "stream_service_get","stream_service_set",
    "studio_set_enabled",
    "profiles_list","profiles_set_current",
    "scene_collections_list","scene_collections_set_current",
    "hotkeys_list","hotkeys_trigger_by_name","hotkeys_trigger_by_keys",
    "screenshot_take",
    # Sequencer
    "sequence_schedule","sequence_cancel","sequence_status",
}


def validate_top_level(params: Dict[str, Any]) -> Tuple[str, Dict[str, Any], bool, int | None, str | None, bool]:
    """Retourne (action, args, wait, timeout_sec, session_id, dry_run)."""
    if not isinstance(params, dict):
        raise ValueError("invalid_parameters")

    action = params.get("action")
    if not isinstance(action, str) or not action:
        raise ValueError("missing_action")
    if action not in ALLOWED_ACTIONS:
        raise ValueError("unknown_action")

    args = params.get("args")
    if args is None:
        args = {}
    if not isinstance(args, dict):
        raise ValueError("invalid_args")

    wait = params.get("wait", True)
    if not isinstance(wait, bool):
        raise ValueError("invalid_wait")

    timeout = params.get("timeout_sec")
    if timeout is not None and (not isinstance(timeout, int) or timeout < 1 or timeout > 60):
        raise ValueError("invalid_timeout")

    session_id = params.get("session_id")
    if session_id is not None and not isinstance(session_id, str):
        raise ValueError("invalid_session_id")

    dry_run = params.get("dry_run", False)
    if not isinstance(dry_run, bool):
        raise ValueError("invalid_dry_run")

    return action, args, wait, timeout, session_id, dry_run


def validate_action_args(action: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Placeholder v1: la validation fine par action sera ajoutée lors de l'implémentation.
    Pour l'instant, on passe-through (validation stricte côté implémentation à venir).
    """
    return args
