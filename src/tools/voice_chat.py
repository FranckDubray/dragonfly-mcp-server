import json, os

def spec():
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'voice_chat.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)

from ._voice_chat.api import route_operation as run
