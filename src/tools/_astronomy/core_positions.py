"""
Positions-related operations (planets and stars)
"""
from __future__ import annotations

from skyfield.api import Star

from .services.skyfield_client import get_ephemeris, get_timescale, create_observer, get_body
from .utils import format_position, calculate_visibility
from .constants import get_star_entry


def planet_position(params: dict) -> dict:
    body = params['body']
    latitude = params['latitude']
    longitude = params['longitude']
    elevation = params['elevation']
    date = params['date']  # datetime (UTC)

    eph = get_ephemeris()
    ts = get_timescale()

    t = ts.from_datetime(date)
    observer = create_observer(latitude, longitude, elevation)

    earth = eph['earth']
    body_obj = get_body(body)

    astrometric = (earth + observer).at(t).observe(body_obj)
    pos = format_position(astrometric, t)

    visibility = calculate_visibility(pos['horizontal']['altitude']['degrees'])

    return {
        'success': True,
        'operation': 'planet_position',
        'body': body,
        'observer': {
            'latitude': latitude,
            'longitude': longitude,
            'elevation_m': elevation,
            'time_utc': t.utc_iso(),
        },
        'position': pos,
        'visibility_status': visibility,
    }


def star_position_operation(params: dict) -> dict:
    """Compute approximate star apparent position from RA/Dec catalog and observer/date.
    Uses a small bright stars catalog. Proper motion/precession ignored for simplicity.
    """
    star_name = params['star_name']
    latitude = params['latitude']
    longitude = params['longitude']
    elevation = params['elevation']
    date = params['date']

    entry = get_star_entry(star_name)
    if not entry:
        return {
            'success': False,
            'error': f"Unknown star: {star_name}. Try common names like 'Sirius', 'Vega', 'Betelgeuse', 'Polaris'."
        }

    ra_hours = float(entry['ra_hours'])
    dec_deg = float(entry['dec_degrees'])

    ts = get_timescale()
    t = ts.from_datetime(date)

    # Skyfield Star from RA hours and Dec degrees
    star = Star(ra_hours=ra_hours, dec_degrees=dec_deg)

    eph = get_ephemeris()
    earth = eph['earth']
    observer = create_observer(latitude, longitude, elevation)

    astrometric = (earth + observer).at(t).observe(star)
    pos = format_position(astrometric, t)

    visibility = calculate_visibility(pos['horizontal']['altitude']['degrees'])

    return {
        'success': True,
        'operation': 'star_position',
        'star': {
            'name': entry['name'],
            'constellation': entry.get('constellation'),
            'magnitude': entry.get('magnitude'),
            'catalog': 'built-in bright_stars (approx)'
        },
        'observer': {
            'latitude': latitude,
            'longitude': longitude,
            'elevation_m': elevation,
            'time_utc': t.utc_iso(),
        },
        'position': pos,
        'visibility_status': visibility,
    }
