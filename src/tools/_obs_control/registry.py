from __future__ import annotations
from typing import Any, Callable, Dict

# Import des domaines core
from .core import status as core_status
from .core import scenes as core_scenes
from .core import screenshot as core_screenshot
from .core import outputs as core_outputs
from .core import outputs_extended as core_outputs_ext
from .core import inputs as core_inputs
from .core import scene_items as core_scene_items
from .core import media as core_media
from .core import filters as core_filters
from .core import transitions as core_transitions
from .core import transitions_override as core_override
from .core import profiles_collections as core_profiles
from .core import hotkeys as core_hotkeys
from .core import studio as core_studio
from .core import system as core_system
from .services import obs_client

# Type du handler standard
Handler = Callable[[Dict[str, Any], bool, int | None, str | None, bool], Dict[str, Any]]


def get_routes() -> Dict[str, Handler]:
    """Retourne la table action -> handler(args, wait, timeout_sec, session_id, dry_run)."""
    return {
        # System / status / screenshot
        "get_version": lambda a,w,t,s,d: core_system.get_version(a),
        "status_snapshot": lambda a,w,t,s,d: core_status.snapshot(session_id=s, timeout_sec=t),
        "screenshot_take": lambda a,w,t,s,d: core_screenshot.take(args=a, session_id=s, timeout_sec=t, dry_run=d),

        # Scenes
        "scenes_list": lambda a,w,t,s,d: core_scenes.list_scenes(a),
        "scenes_set_current": lambda a,w,t,s,d: core_scenes.set_current(args=a, session_id=s, wait=w, timeout_sec=t, dry_run=d),
        "scenes_set_preview": lambda a,w,t,s,d: core_scenes.set_preview(args=a, session_id=s, timeout_sec=t, dry_run=d),
        "scenes_transition_to_program": lambda a,w,t,s,d: core_scenes.transition_to_program(args=a, session_id=s, wait=w, timeout_sec=t),
        "scenes_create": lambda a,w,t,s,d: core_scenes.create(a),
        "scenes_delete": lambda a,w,t,s,d: core_scenes.delete(a),
        "scenes_rename": lambda a,w,t,s,d: core_scenes.rename(a),
        "scenes_set_default_transition": lambda a,w,t,s,d: core_scenes.set_default_transition(a),
        "scene_transition_override_get": lambda a,w,t,s,d: core_override.override_get(a),
        "scene_transition_override_set": lambda a,w,t,s,d: core_override.override_set(a),

        # Scene items
        "scene_items_list": lambda a,w,t,s,d: core_scene_items.list_items(a),
        "scene_items_set_enabled": lambda a,w,t,s,d: core_scene_items.set_enabled(a),
        "scene_items_set_transform": lambda a,w,t,s,d: core_scene_items.set_transform(a),
        "scene_items_set_order": lambda a,w,t,s,d: core_scene_items.set_order(a),
        "scene_items_add": lambda a,w,t,s,d: core_scene_items.add(a),
        "scene_items_remove": lambda a,w,t,s,d: core_scene_items.remove(a),
        "scene_item_set_locked": lambda a,w,t,s,d: core_scene_items.set_locked(a),

        # Inputs
        "inputs_list": lambda a,w,t,s,d: core_inputs.inputs_list(a),
        "inputs_kind_list": lambda a,w,t,s,d: core_inputs.inputs_kind_list(a),
        "inputs_create": lambda a,w,t,s,d: core_inputs.create(a),
        "inputs_remove": lambda a,w,t,s,d: core_inputs.remove(a),
        "inputs_rename": lambda a,w,t,s,d: core_inputs.rename(a),
        "inputs_get_settings": lambda a,w,t,s,d: core_inputs.get_settings(a),
        "inputs_set_settings": lambda a,w,t,s,d: core_inputs.set_settings(a),
        "inputs_set_mute": lambda a,w,t,s,d: core_inputs.set_mute(a),
        "inputs_set_volume": lambda a,w,t,s,d: core_inputs.set_volume(a),
        "inputs_set_monitor_type": lambda a,w,t,s,d: core_inputs.set_monitor_type(a),
        "inputs_press_button": lambda a,w,t,s,d: core_inputs.press_button(a),

        # Media
        "media_status": lambda a,w,t,s,d: core_media.status(a),
        "media_action": lambda a,w,t,s,d: core_media.action(a, wait=w, timeout_sec=t),
        "media_seek": lambda a,w,t,s,d: core_media.seek(a),

        # Audio avancé
        "audio_balance_set": lambda a,w,t,s,d: __import__(__name__.replace("registry","core.audio"), fromlist=["x"]).balance_set(a),
        "audio_sync_offset_set": lambda a,w,t,s,d: __import__(__name__.replace("registry","core.audio"), fromlist=["x"]).sync_offset_set(a),

        # Filters
        "filters_list": lambda a,w,t,s,d: core_filters.list_filters(a),
        "filters_add": lambda a,w,t,s,d: core_filters.add(a),
        "filters_remove": lambda a,w,t,s,d: core_filters.remove(a),
        "filters_rename": lambda a,w,t,s,d: core_filters.rename(a),
        "filters_set_enabled": lambda a,w,t,s,d: core_filters.set_enabled(a),
        "filters_set_settings": lambda a,w,t,s,d: core_filters.set_settings(a),

        # Transitions
        "transitions_get_list": lambda a,w,t,s,d: core_transitions.get_list(a),
        "transitions_get_current": lambda a,w,t,s,d: core_transitions.get_current(a),
        "transitions_get_duration": lambda a,w,t,s,d: core_transitions.get_duration(a),
        "transitions_set_duration": lambda a,w,t,s,d: core_transitions.set_duration(a),
        "transitions_set_current": lambda a,w,t,s,d: core_transitions.set_current(a),

        # Outputs stream
        "outputs_stream_status": lambda a,w,t,s,d: core_outputs.stream_status(session_id=s, timeout_sec=t),
        "outputs_stream_start": lambda a,w,t,s,d: core_outputs.stream_start(args=a, session_id=s, wait=w, timeout_sec=t, dry_run=d),
        "outputs_stream_stop": lambda a,w,t,s,d: core_outputs.stream_stop(args=a, session_id=s, wait=w, timeout_sec=t, dry_run=d),

        # Outputs étendus
        "outputs_record_start": lambda a,w,t,s,d: core_outputs_ext.record_start(a),
        "outputs_record_stop": lambda a,w,t,s,d: core_outputs_ext.record_stop(a),
        "outputs_record_pause": lambda a,w,t,s,d: core_outputs_ext.record_pause(a),
        "outputs_record_resume": lambda a,w,t,s,d: core_outputs_ext.record_resume(a),
        "outputs_record_status": lambda a,w,t,s,d: core_outputs_ext.record_status(a),
        "outputs_replay_start": lambda a,w,t,s,d: core_outputs_ext.replay_start(a),
        "outputs_replay_stop": lambda a,w,t,s,d: core_outputs_ext.replay_stop(a),
        "outputs_replay_save": lambda a,w,t,s,d: core_outputs_ext.replay_save(a),
        "outputs_replay_status": lambda a,w,t,s,d: core_outputs_ext.replay_status(a),
        "outputs_virtualcam_start": lambda a,w,t,s,d: core_outputs_ext.virtualcam_start(a),
        "outputs_virtualcam_stop": lambda a,w,t,s,d: core_outputs_ext.virtualcam_stop(a),
        "outputs_virtualcam_status": lambda a,w,t,s,d: core_outputs_ext.virtualcam_status(a),
        "stream_service_get": lambda a,w,t,s,d: core_outputs_ext.stream_service_get(a),
        "stream_service_set": lambda a,w,t,s,d: core_outputs_ext.stream_service_set(a),

        # Profiles / Collections
        "profiles_list": lambda a,w,t,s,d: core_profiles.profiles_list(a),
        "profiles_set_current": lambda a,w,t,s,d: core_profiles.profiles_set_current(a),
        "scene_collections_list": lambda a,w,t,s,d: core_profiles.scene_collections_list(a),
        "scene_collections_set_current": lambda a,w,t,s,d: core_profiles.scene_collections_set_current(a),

        # Hotkeys
        "hotkeys_list": lambda a,w,t,s,d: core_hotkeys.list_hotkeys(a),
        "hotkeys_trigger_by_name": lambda a,w,t,s,d: core_hotkeys.trigger_by_name(a),
        "hotkeys_trigger_by_keys": lambda a,w,t,s,d: core_hotkeys.trigger_by_keys(a),

        # Studio
        "studio_set_enabled": lambda a,w,t,s,d: core_studio.set_enabled(a),

        # Raw
        "raw_request": lambda a,w,t,s,d: obs_client.call(a.get("request_type"), a.get("request_data")) if isinstance(a, dict) else {"ok": False, "error": "invalid_argument"},
    }
