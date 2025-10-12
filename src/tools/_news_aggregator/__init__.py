"""News Aggregator package."""
import json
import os


def spec():
    """Load canonical JSON spec."""
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', '..', 'tool_specs', 'news_aggregator.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)
