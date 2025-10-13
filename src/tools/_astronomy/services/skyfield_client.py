"""
Skyfield client for astronomy calculations
Handles ephemeris loading and caching
"""

from skyfield.api import Loader, wgs84
from skyfield.almanac import moon_phase, sunrise_sunset, dark_twilight_day
import os

# Global cache for ephemeris and timescale
_ephemeris = None
_timescale = None
_loader = None


def get_data_dir() -> str:
    """Return project data directory for astronomy assets (ephemeris, TLE, catalogs).
    Location: <repo>/docs/astronomy
    """
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
    )
    return os.path.join(project_root, 'docs', 'astronomy')


def get_loader():
    """Get or create Skyfield loader with custom directory"""
    global _loader
    if _loader is None:
        ephemeris_dir = get_data_dir()
        os.makedirs(ephemeris_dir, exist_ok=True)
        _loader = Loader(ephemeris_dir)
    return _loader


def get_timescale():
    """Get or create timescale (cached)"""
    global _timescale
    if _timescale is None:
        loader = get_loader()
        _timescale = loader.timescale()
    return _timescale


def get_ephemeris():
    """Get or create ephemeris (cached)
    Uses de421.bsp (JPL Development Ephemeris 421)
    Covers years 1900-2050
    Downloaded to docs/astronomy/ on first use
    """
    global _ephemeris
    if _ephemeris is None:
        loader = get_loader()
        # Load from cache or download to docs/astronomy/
        _ephemeris = loader('de421.bsp')
    return _ephemeris


def create_observer(latitude, longitude, elevation=0):
    """Create observer position
    
    Args:
        latitude: Latitude in degrees
        longitude: Longitude in degrees
        elevation: Elevation in meters (default: 0)
        
    Returns:
        GeographicPosition object
    """
    return wgs84.latlon(latitude, longitude, elevation_m=elevation)


def get_body(body_name):
    """Get celestial body from ephemeris
    
    Args:
        body_name: Body name (sun, moon, mercury, venus, mars, etc.)
        
    Returns:
        Skyfield body object
        
    Raises:
        ValueError: If body not found
    """
    eph = get_ephemeris()
    
    # Normalize name
    body_name = body_name.lower().strip()
    
    # Map to ephemeris names
    body_map = {
        'sun': 'sun',
        'moon': 'moon',
        'mercury': 'mercury',
        'venus': 'venus',
        'mars': 'mars',
        'jupiter': 'jupiter barycenter',
        'saturn': 'saturn barycenter',
        'uranus': 'uranus barycenter',
        'neptune': 'neptune barycenter',
        'pluto': 'pluto barycenter',
        'earth': 'earth'
    }
    
    if body_name not in body_map:
        raise ValueError(f"Unknown body: {body_name}")
    
    eph_name = body_map[body_name]
    return eph[eph_name]


def calculate_moon_phase(time):
    """Calculate moon phase
    
    Args:
        time: Skyfield Time object
        
    Returns:
        dict with phase information
    """
    eph = get_ephemeris()
    
    # Calculate phase angle
    phase_angle = moon_phase(eph, time)
    
    # Calculate illumination percentage
    illumination = 100 * (1 + phase_angle.degrees / 180) / 2
    
    # Determine phase name
    phase_idx = int((phase_angle.degrees + 22.5) / 45) % 8
    from ..constants import MOON_PHASES
    phase_name = MOON_PHASES[phase_idx]
    
    return {
        'phase_angle_degrees': round(phase_angle.degrees, 2),
        'illumination_percent': round(illumination, 1),
        'phase_name': phase_name
    }
