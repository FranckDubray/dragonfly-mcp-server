"""
Core astronomy calculation logic (facade)
Split into focused modules to keep files <7KB as per policy
"""

from .core_positions import planet_position, star_position_operation
from .core_times import moon_phase_operation, sun_moon_times_operation
from .core_events import celestial_events_operation, visible_planets_operation, iss_position_operation

__all__ = [
    "planet_position",
    "moon_phase_operation",
    "sun_moon_times_operation",
    "celestial_events_operation",
    "planet_info_operation",
    "visible_planets_operation",
    "iss_position_operation",
    "star_position_operation",
]

from .constants import get_planet_data
from .utils import format_physical_data


def planet_info_operation(params):
    body_name = params['body']
    data = get_planet_data().get(body_name)
    if not data:
        return {"success": False, "error": f"No data available for body: {body_name}"}
    formatted = format_physical_data(data)
    return {
        "success": True,
        "operation": "planet_info",
        "body": body_name,
        "data": formatted,
        "source": "NASA Planetary Fact Sheets",
    }
