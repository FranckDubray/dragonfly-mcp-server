"""
ffmpeg_frames MCP Tool (coarse smoothing + native refinement, start/end only)
- Coarse: RGB24 @ 12fps, 24x24, EMA fast/slow + residual R_t + median filter, hysteresis thresholds + NMS
- Refine: native FPS window, exact cut localization; export 2 images per plan (start/end)
- Debug: diffs (coarse), r_values (coarse), thresholds, refined cuts, scene durations
NOTE: Aucune contrainte max 15s codée — 15s est un indicateur d'évaluation seulement (report dans debug.json)
"""
from __future__ import annotations
import os, json
from typing import Dict, Any, List
from ._ffmpeg import paths as ffpaths
from ._ffmpeg import detect as ffdetect
from ._ffmpeg import extract as ffextract
from ._ffmpeg import timestamps as ffts

# Coarse params (internes)
_ANALYZE_FPS = 12.0
_SIM_SCALE_W = 24
_SIM_SCALE_H = 24
_SIM_THRESHOLD = 0.25  # floor; dyn thresholds via P60/P80 on residual R_t
_HARD_CUT_THRESHOLD = 0.60
_MIN_SCENE_FRAMES = 6


def run(operation: str = None, **params):
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

    # 1) Coarse detection with smoothing + hysteresis
    info = ffdetect.detect_cuts_similarity_info(
        path_abs,
        analyze_fps=_ANALYZE_FPS,
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

    # 3) Refine at native FPS
    refined = ffdetect.refine_cuts_native(
        path_abs,
        cuts_with_strength=[(t, 1.0) for t in cuts_pruned],
        fps_native=avg_fps,
        duration=duration,
        window_sec=0.33,
    )
    cuts = [x['time'] for x in refined]

    # 4) Build scenes and export strictly start/end per scene
    shots = ffts.build_shots_with_labels(cuts, duration, 0, end_eps=0.0)
    frames = ffextract.extract_shots_labeled(path_abs, outdir_abs, shots, image_format, overwrite)

    # Debug manifest (inclut métriques d'évaluation, pas d'enforcement)
    try:
        # Durées par plan et métriques (min/median/max, count > 15s)
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
            'avg_fps': avg_fps,
            'min_scene_sec': min_scene_sec,
            'thresholds': info.get('thresholds'),
            'coarse_frames_analyzed': info.get('frames_analyzed'),
            'coarse_time_sec': info.get('time_sec'),
            'diffs': info.get('diffs'),        # capped
            'r_values': info.get('r_values'),  # capped residuals
            'cuts_coarse': cuts_coarse,
            'cuts_pruned': cuts_pruned,
            'cuts_refined': refined,
            'scenes': [{'index': s['index'], 'start': s['start'], 'end': s['end']} for s in shots],
            'scene_duration_stats': stats
        }
        os.makedirs(outdir_abs, exist_ok=True)
        with open(os.path.join(outdir_abs, 'debug.json'), 'w') as f:
            json.dump(man, f)
    except Exception:
        pass

    return {
        'success': True,
        'mode_used': 'coarse_smooth_native_refine_start_end',
        'duration': duration,
        'avg_fps': avg_fps,
        'min_scene_sec': min_scene_sec,
        'scenes_count': len(cuts),
        'frames': frames,
        'output_dir': output_dir
    }


def spec():
    return {
        'type': 'function',
        'function': {
            'name': 'ffmpeg_frames',
            'displayName': 'FFmpeg Frames',
            'description': "2 images par plan (start/end) avec lissage coarse + raffinement natif, debug des similarités.",
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
