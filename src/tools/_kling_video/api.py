import os
import time
import json
import sys
import subprocess
from typing import Any, Dict

from .validators import validate_params, ValidationError
from .core import create_task, get_status, list_tasks, download_video, KlingApiError


def _format_error(e: Exception) -> Dict[str, Any]:
    if isinstance(e, ValidationError):
        return {"ok": False, "error": {"type": "validation_error", "message": str(e)}}
    if isinstance(e, KlingApiError):
        payload = e.args[0] if e.args else {"message": str(e)}
        if isinstance(payload, dict):
            return {"ok": False, "error": {"type": "api_error", "provider": "kling", **payload}}
        return {"ok": False, "error": {"type": "api_error", "provider": "kling", "detail": str(e)}}
    return {"ok": False, "error": {"type": "unknown_error", "message": str(e)}}


def _auto_start_play(path: str) -> dict:
    if not path or not os.path.isfile(path):
        return {"ok": False, "error": {"type": "file_error", "message": f"File not found: {path}"}}
    try:
        if sys.platform.startswith('darwin'):
            subprocess.Popen(['open', path])
        elif os.name == 'nt':
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(['xdg-open', path])
        return {"ok": True, "path": path, "started": True}
    except Exception as e:
        return {"ok": False, "error": {"type": "launch_error", "message": str(e)}}


def run(**params) -> Any:
    try:
        params = validate_params(params)
        op = params['operation']

        if op == 'auto_start':
            # Either play a provided path or download first then play
            path = params.get('path')
            if path:
                return _auto_start_play(path)
            # if a task_id/external_task_id is given, download it first
            if not params.get('task_id') and not params.get('external_task_id'):
                return {"ok": False, "error": {"type": "validation_error", "message": "task_id|external_task_id or path is required for auto_start"}}
            gm = params.get('generation_mode') or 'text2video'
            stat = get_status(gm, task_id=params.get('task_id'), external_task_id=params.get('external_task_id'))
            path, thumb = download_video(stat, filename=params.get('filename'), overwrite=params.get('overwrite', False))
            return _auto_start_play(path)

        if op == 'create':
            generation_mode = params['generation_mode']
            wait = params.get('wait', False)
            max_attempts = params.get('max_attempts', 60)
            timeout_seconds = params.get('timeout_seconds', 600)
            auto_download = params.get('auto_download', False)
            overwrite = params.get('overwrite', False)
            filename = params.get('filename')

            resp = create_task(generation_mode, params)
            data = resp.get('data') or {}
            task_id = data.get('task_id')
            out = {
                'task_id': task_id,
                'task_status': data.get('task_status'),
                'created_at': data.get('created_at'),
                'updated_at': data.get('updated_at'),
            }
            if not wait:
                return out

            # Wait
            start = time.time()
            attempts = 0
            last = None
            while attempts < max_attempts and (time.time() - start) < timeout_seconds:
                last = get_status(generation_mode, task_id=task_id, external_task_id=params.get('external_task_id'))
                d = last.get('data') or {}
                st = d.get('task_status')
                if st in ('succeed', 'failed'):
                    if st == 'succeed' and auto_download:
                        video_path, thumb_path = download_video(last, filename=filename, overwrite=overwrite)
                        return {
                            'final_status': 'succeed',
                            'task_id': task_id,
                            'path': video_path,
                            'thumbnail_path': thumb_path,
                        }
                    return {
                        'final_status': st,
                        'task_id': task_id,
                        'task_status_msg': d.get('task_status_msg')
                    }
                attempts += 1
                # adaptive spacing
                remain = max(0.0, timeout_seconds - (time.time() - start))
                left = max(1, max_attempts - attempts)
                gap = max(1.0, remain / left)
                time.sleep(min(gap, 5.0))

            return {
                'final_status': 'processing',
                'attempts_done': attempts,
                'elapsed_seconds': int(time.time() - start),
                'task_id': task_id,
                'warning': 'timeout'
            }

        if op == 'get_status':
            gm = params.get('generation_mode') or 'text2video'
            return get_status(gm, task_id=params.get('task_id'), external_task_id=params.get('external_task_id'))

        if op == 'list':
            gm = params.get('generation_mode') or 'text2video'
            page = params.get('page', 1)
            limit = params.get('limit', 20)
            resp = list_tasks(gm, page=page, page_size=limit)
            data = resp.get('data') or []
            return {
                'items': data,
                'returned_count': len(data),
                'truncated': len(data) >= limit
            }

        if op == 'download':
            gm = params.get('generation_mode') or 'text2video'
            stat = get_status(gm, task_id=params.get('task_id'), external_task_id=params.get('external_task_id'))
            path, thumb = download_video(stat, filename=params.get('filename'), overwrite=params.get('overwrite', False))
            return {'path': path, 'thumbnail_path': thumb}

        raise ValueError(f'Unsupported operation: {op}')
    except Exception as e:
        return _format_error(e)
