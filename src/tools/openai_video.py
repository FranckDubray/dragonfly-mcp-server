import json, os


def spec():
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'openai_video.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run(**params):
    # Delegate to implementation package (no side effects at import time for external I/O)
    from ._openai_video.api import run as impl_run
    return impl_run(**params)
