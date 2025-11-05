import json, os
from _veo_video.api import run as _run

def spec():
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'veo_video.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run(**params):
    return _run(**params)
