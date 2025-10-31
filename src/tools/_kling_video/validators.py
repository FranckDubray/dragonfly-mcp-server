import os
from typing import Any, Dict, List

from .utils import DOCS_IMAGES_DIR, resolve_under

ALLOWED_MODELS = {
    'kling-v1', 'kling-v1-5', 'kling-v1-6',
    'kling-v2-master', 'kling-v2-1', 'kling-v2-1-master', 'kling-v2-5-turbo'
}
ALLOWED_MODES = {'std', 'pro'}
ALLOWED_ASPECTS = {'16:9', '9:16', '1:1'}

class ValidationError(ValueError):
    pass


def _require_prompt(params: Dict[str, Any]) -> None:
    p = params.get('prompt')
    if not isinstance(p, str) or not p.strip():
        raise ValidationError('prompt (string) is required')


def _validate_local_image(path: str) -> None:
    abs_path = resolve_under(DOCS_IMAGES_DIR, path)
    if not os.path.isfile(abs_path):
        raise ValidationError(f'image file not found under docs/images: {path}')
    low = abs_path.lower()
    if not (low.endswith('.jpg') or low.endswith('.jpeg') or low.endswith('.png')):
        raise ValidationError('image must be .jpg/.jpeg/.png')


def validate_params(params: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(params, dict):
        raise ValidationError('params must be an object')

    op = params.get('operation')
    if op not in {'create', 'get_status', 'list', 'download'}:
        raise ValidationError('operation must be one of create|get_status|list|download')

    if op == 'create':
        mode = params.get('generation_mode')
        if mode not in {'text2video', 'image2video', 'multi_image2video'}:
            raise ValidationError('generation_mode must be text2video|image2video|multi_image2video')

        model = params.get('model_name', 'kling-v1-6')
        if model not in ALLOWED_MODELS:
            raise ValidationError('model_name invalid')

        run_mode = params.get('mode', 'std')
        if run_mode not in ALLOWED_MODES:
            raise ValidationError('mode must be std or pro')

        duration = params.get('duration', 5)
        if duration not in {5, 10}:
            raise ValidationError('duration must be 5 or 10 seconds')

        _require_prompt(params)

        # v2.x: cfg_scale not supported
        if model.startswith('kling-v2') and 'cfg_scale' in params and params['cfg_scale'] is not None:
            raise ValidationError('cfg_scale is not supported on kling-v2.x models')

        # camera_control: if type == simple, ensure only one non-zero in config
        cc = params.get('camera_control')
        if cc:
            ctype = cc.get('type')
            if ctype not in {None, 'simple', 'down_back', 'forward_up', 'right_turn_forward', 'left_turn_forward'}:
                raise ValidationError('camera_control.type invalid')
            if ctype == 'simple':
                conf = cc.get('config') or {}
                non_zero = sum(1 for k in ['horizontal','vertical','pan','tilt','roll','zoom'] if conf.get(k) not in (None, 0, 0.0))
                if non_zero != 1:
                    raise ValidationError('camera_control.config: exactly one of horizontal|vertical|pan|tilt|roll|zoom must be non-zero for type=simple')
            else:
                if cc.get('config'):
                    raise ValidationError('camera_control.config must be empty unless type=simple')

        if mode == 'text2video':
            ar = params.get('aspect_ratio', '16:9')
            if ar not in ALLOWED_ASPECTS:
                raise ValidationError('aspect_ratio must be 16:9|9:16|1:1')

        elif mode == 'image2video':
            img = params.get('image')
            img_tail = params.get('image_tail')
            if not img and not img_tail:
                raise ValidationError('image2video requires at least image or image_tail')
            # Mutual exclusions: image_tail vs masks vs camera_control
            if img_tail and (params.get('static_mask') or params.get('dynamic_masks') or params.get('camera_control')):
                raise ValidationError('image_tail cannot be used with static_mask/dynamic_masks or camera_control')
            # start/end gating (kling-v2-1 pro 5s/10s)
            if img_tail:
                if not (model == 'kling-v2-1' and run_mode == 'pro' and duration in {5,10}):
                    raise ValidationError('image_tail supported only on kling-v2-1 with mode=pro and duration 5 or 10')
            # local file checks
            if img and not img.startswith('http'): _validate_local_image(img)
            if img_tail and not img_tail.startswith('http'): _validate_local_image(img_tail)

            # masks: only kling-v1 std/pro 5s
            if params.get('static_mask') or params.get('dynamic_masks'):
                if not (model == 'kling-v1' and duration == 5):
                    raise ValidationError('dynamic/static mask only supported on kling-v1 with duration=5')

        else:  # multi_image2video
            images = params.get('image_list') or []
            if not isinstance(images, list) or not (1 <= len(images) <= 4):
                raise ValidationError('image_list must have 1..4 items')
            for it in images:
                if not isinstance(it, str):
                    raise ValidationError('image_list items must be strings (path or URL)')
                if not it.startswith('http'):
                    _validate_local_image(it)
            ar = params.get('aspect_ratio', '16:9')
            if ar not in ALLOWED_ASPECTS:
                raise ValidationError('aspect_ratio must be 16:9|9:16|1:1')

        # wait controls
        if params.get('wait'):
            ma = params.get('max_attempts', 60)
            to = params.get('timeout_seconds', 600)
            if not (isinstance(ma, int) and 1 <= ma <= 600):
                raise ValidationError('max_attempts must be 1..600')
            if not (isinstance(to, int) and 1 <= to <= 3600):
                raise ValidationError('timeout_seconds must be 1..3600')

    elif op == 'get_status' or op == 'download':
        if not params.get('task_id') and not params.get('external_task_id'):
            raise ValidationError('task_id or external_task_id is required')

    elif op == 'list':
        page = params.get('page', 1)
        limit = params.get('limit', 20)
        if not (isinstance(page, int) and page >= 1):
            raise ValidationError('page must be >= 1')
        if not (isinstance(limit, int) and 1 <= limit <= 100):
            raise ValidationError('limit must be 1..100')

    return params
