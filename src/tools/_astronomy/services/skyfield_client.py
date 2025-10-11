"""
Skyfield client for astronomy calculations
Handles ephemeris loading and caching
"""

from skyfield.api import load, wgs84, Star
from skyfield.almanac import moon_phase, sunrise_sunset, dark_twilight_day
from skyfield.toposlib import GeographicPosition
import os

# Global cache for ephemeris and timescale
_ephemeris = None
_timescale = None
_stars = None
_loader = None


def get_loader():
    """Get or create Skyfield loader with custom directory"""
    global _loader
    if _loader is None:
        # Use docs/astronomy for ephemeris data (not src/)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
        ephemeris_dir = os.path.join(project_root, 'docs', 'astronomy')
        
        # Create directory if it doesn't exist
        os.makedirs(ephemeris_dir, exist_ok=True)
        
        # Create loader with custom directory
        _loader = load(ephemeris_dir)
    
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


def get_stars():
    """Get star catalog (cached)"""
    global _stars
    if _stars is None:
        loader = get_loader()
        _stars = loader('hip_main.dat')
    return _stars


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


def get_star_by_name(star_name):
    """Get star by name from Hipparcos catalog
    
    Args:
        star_name: Star name (Sirius, Vega, etc.)
        
    Returns:
        Star object
        
    Raises:
        ValueError: If star not found
    """
    from ..constants import BRIGHT_STARS
    
    star_name_lower = star_name.lower().strip()
    
    if star_name_lower not in BRIGHT_STARS:
        raise ValueError(
            f"Star '{star_name}' not found. Available stars: {', '.join(BRIGHT_STARS.keys())}"
        )
    
    # For bright stars, we use their known positions
    # In a full implementation, you'd query the Hipparcos catalog
    # For now, we'll create a Star object with approximate data
    star_info = BRIGHT_STARS[star_name_lower]
    
    # Note: This is a simplified implementation
    # A full version would load actual RA/Dec from Hipparcos catalog
    return star_info


def calculate_moon_phase(time):
    """Calculate moon phase
    
    Args:
        time: Skyfield Time object
        
    Returns:
        dict with phase information
    """
    eph = get_ephemeris()
    earth = eph['earth']
    moon = eph['moon']
    sun = eph['sun']
    
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


def calculate_rise_set(observer, body, date):
    """Calculate rise and set times for a body
    
    Args:
        observer: GeographicPosition
        body: Celestial body
        date: Date for calculation (datetime)
        
    Returns:
        dict with rise/set times
    """
    ts = get_timescale()
    eph = get_ephemeris()
    
    # Create time range (24 hours from date)
    t0 = ts.utc(date.year, date.month, date.day, 0, 0, 0)
    t1 = ts.utc(date.year, date.month, date.day, 23, 59, 59)
    
    # Calculate rise/set
    earth = eph['earth']
    location = earth + observer
    
    # Find rise and set events
    f = sunrise_sunset(eph, location)
    times, events = f(t0, t1)
    
    result = {
        'rise_time': None,
        'set_time': None,
        'transit_time': None
    }
    
    for t, e in zip(times, events):
        if e == 1:  # Rise
            result['rise_time'] = t.utc_iso()
        elif e == 0:  # Set
            result['set_time'] = t.utc_iso()
    
    return result
