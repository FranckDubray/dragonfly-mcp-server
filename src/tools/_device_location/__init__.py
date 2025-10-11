"""
Device Location Tool - Get GPS coordinates and location info for the current device.
Uses IP-based geolocation (free, no API key required).
"""
import json
import os


def spec():
    """Load and return the canonical JSON spec."""
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', '..', 'tool_specs', 'device_location.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)
