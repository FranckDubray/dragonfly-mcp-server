"""Ollama Local package."""
import json
import os


def spec():
    """Load and return the JSON specification."""
    here = os.path.dirname(__file__)
    spec_path = os.path.join(here, '..', '..', 'tool_specs', 'ollama_local.json')
    spec_path = os.path.abspath(spec_path)
    
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)