
<<<<<<< HEAD









=======
>>>>>>> 464278b4ec6642822325a0a46d7a1312564e1550
"""
ffmpeg_frames MCP Tool (native frame-by-frame + moving average + hysteresis, start/end only)
- Native: PyAV decoding @ fps natif, 96x96 gray, diff L1 frame->frame
- Lissage: moyenne mobile (ma_window=1), hystérésis (P75/P95) + NMS 0.2s
- Raffinement: natif (PyAV) dans une fenêtre ±0.5s (fallback: pas de raffinement)
- Export: 2 images par plan (start/end)
- Debug: frames_debug (t, diff, similarity_pct), avg_similarity_pct, diffs, r_values, thresholds
"""
from __future__ import annotations
import os, json, time
from typing import Dict, Any, List
from ._ffmpeg import paths as ffpaths
from ._ffmpeg import detect as ffdetect
from ._ffmpeg import native as ffnative
from ._ffmpeg import extract as ffextract
from ._ffmpeg import timestamps as ffts

# Params (sensibilité haute par défaut)
_SIM_SCALE_W = 96
_SIM_SCALE_H = 96
_SIM_THRESHOLD = 0.05  # floor; dynamic thresholds via percentiles sur R
_HARD_CUT_THRESHOLD = 0.50
_MIN_SCENE_FRAMES = 3
_MA_WINDOW = 1
_REFINE_WINDOW_SEC = 0.5


def run(operation: str = None, **params):
    t0 = time.monotonic()

    if operation != 'extract_frames':
        return {"error": f"Unsupported operation: {operation}"}

    raw_path = params.get('path')
    if not raw_path:
        return {"success": False, "error": "path is required"}
    rel_path = ffpaths.rel_video_path(raw_path)

    if not rel_path.startswith('docs/video/'):
        return {"success": False, "error": "Only files under docs/video are allowed."}

    path_abs = ffpaths.abs_from_project(rel_path)
    if not os.path.exists(path_abs):
        return {"success": False, "error": f"File not found: {raw_path}"}

    output_dir = params.get('output_dir') or (os.path.splitext(rel_path)[0] + '_frames')
    if output_dir.startswith('/'):
        output_dir = output_dir[1:]
    outdir_abs = ffpaths.abs_from_project(output_dir)

    overwrite = bool(params.get('overwrite', True))
    image_format = 'jpg'

    duration = ffdetect.probe_duration(path_abs)
    avg_fps = ffdetect.get_avg_fps(path_abs)
    min_scene_sec = max(0.02, _MIN_SCENE_FRAMES / max(1.0, avg_fps))

    used_native = True
    # 1) Native detection (frame-by-frame, MA + hystérésis)
    info = ffdetect.detect_cuts_similarity_info_native(
        path_abs,
        scale_w=_SIM_SCALE_W,
        scale_h=_SIM_SCALE_H,
        ma_window=_MA_WINDOW,
        threshold_floor=_SIM_THRESHOLD,
    )
    if info.get('error') or not info.get('frames_analyzed'):
        # Fallback legacy coarse (CLI)
        used_native = False
        info = ffdetect.detect_cuts_similarity_info(
            path_abs,
            analyze_fps=max(12.0, min(30.0, avg_fps or 24.0)),
            scale_w=_SIM_SCALE_W,
            scale_h=_SIM_SCALE_H,
            threshold_floor=_SIM_THRESHOLD,
        )
    cuts_coarse = info.get('cuts', [])  # list of (t, score_like)

    # 2) Pruning min scene length (keep hard cuts)
    cuts_pruned = ffts.prune_cuts_min_scene_hardaware(
        cuts_coarse,
        duration,
        min_scene_sec=min_scene_sec,
        hard_threshold=_HARD_CUT_THRESHOLD,
    )

    # 3) Refine
    if used_native:
        refined = ffnative.refine_cuts_native(
            path_abs,
            cuts_with_strength=[(t, 1.0) for t in cuts_pruned],
            duration=duration,
            window_sec=_REFINE_WINDOW_SEC,
            scale=64,
        )
    else:
        # No native refine available: keep coarse times as refined
        refined = [{
            'time': round(t, 6),
            'best_diff': s,
            'window_start': max(0.0, t - _REFINE_WINDOW_SEC),
            'fps': None,
            'local_diffs': []
        } for (t, s) in cuts_pruned]

    cuts = [x['time'] for x in refined]

    # 4) Build scenes and export strictly start/end per scene
    shots = ffts.build_shots_with_labels(cuts, duration, 0, end_eps=0.05)
    frames = ffextract.extract_shots_labeled(path_abs, outdir_abs, shots, image_format, overwrite)

    # Debug manifest riche
    exec_time = round(time.monotonic() - t0, 3)
    try:
        durations = [round(s['end'] - s['start'], 6) for s in shots]
        if durations:
            sorted_d = sorted(durations)
            mid = sorted_d[len(sorted_d)//2]
            stats = {
                'min': min(durations),
                'median': mid,
                'max': max(durations),
                'count_over_15s': sum(1 for d in durations if d > 15.0)
            }
        else:
            stats = {'min': 0.0, 'median': 0.0, 'max': 0.0, 'count_over_15s': 0}
        man = {
            'avg_fps_probe': avg_fps,
            'native_analyzed_fps': info.get('analyzed_fps'),
            'used_native': used_native,
            'min_scene_sec': min_scene_sec,
            'thresholds': info.get('thresholds'),
            'avg_similarity_pct': info.get('avg_similarity_pct'),
            'coarse_frames_analyzed': info.get('frames_analyzed'),
            'coarse_time_sec': info.get('time_sec'),
            'frames_debug': info.get('frames_debug'),  # frame-by-frame: t, diff, similarity_pct
            'diffs': info.get('diffs'),        # capped
            'r_values': info.get('r_values'),  # capped residuals
            'cuts_coarse': cuts_coarse,
            'cuts_pruned': cuts_pruned,
            'cuts_refined': refined,
            'scenes': [{'index': s['index'], 'start': s['start'], 'end': s['end']} for s in shots],
            'scene_duration_stats': stats,
            'exec_time_sec': exec_time
        }
        os.makedirs(outdir_abs, exist_ok=True)
        with open(os.path.join(outdir_abs, 'debug.json'), 'w') as f:
            json.dump(man, f)
    except Exception:
        pass

    return {
        'success': True,
        'mode_used': 'native_frame_by_frame_ma_hysteresis_refine_v1' if used_native else 'legacy_coarse_cli_hysteresis_no_refine',
        'duration': duration,
        'avg_fps_probe': avg_fps,
        'native_analyzed_fps': info.get('analyzed_fps'),
        'min_scene_sec': min_scene_sec,
        'scenes_count': len(cuts),
        'frames': frames,
        'output_dir': output_dir,
        'exec_time_sec': exec_time
    }


def spec():
<<<<<<< HEAD
    """Load and return the canonical JSON spec (source of truth)."""
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'ffmpeg_frames.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)


 
 
 
 
 
 
 
 
 
=======
    return {
        'type': 'function',
        'function': {
            'name': 'ffmpeg_frames',
            'displayName': 'FFmpeg Frames',
            'description': "2 images par plan (start/end) avec détection native frame-by-frame (MA + hystérésis), raffinement natif si dispo, debug complet.",
            'parameters': {
                'type': 'object',
                'properties': {
                    'operation': { 'type': 'string', 'enum': ['extract_frames'] },
                    'path': { 'type': 'string', 'description': 'Chemin de la vidéo sous docs/video/' },
                    'output_dir': { 'type': 'string', 'description': 'Dossier de sortie (optionnel)' },
                    'overwrite': { 'type': 'boolean', 'default': True }
                },
                'required': ['operation','path'],
                'additionalProperties': False
            }
        }
    }

>>>>>>> 464278b4ec6642822325a0a46d7a1312564e1550
