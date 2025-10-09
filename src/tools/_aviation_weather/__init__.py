"""
Aviation Weather tool - Upper air weather data via Open-Meteo API.
"""
import json
import os

def spec():
    """Load canonical JSON spec."""
    spec_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        '..',
        'tool_specs',
        'aviation_weather.json'
    )
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)
