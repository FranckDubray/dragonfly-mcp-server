"""
Events and visibility utilities: celestial events, visible planets, ISS placeholder
"""
from __future__ import annotations

from datetime import timedelta

from .services.skyfield_client import get_ephemeris, get_timescale, create_observer, get_body
from .utils import calculate_angular_separation, degrees_to_cardinal


DEFAULT_HOUR_UTC = 21  # 21:00 UTC snapshot used for visibility checks


def celestial_events_operation(params: dict) -> dict:
    date = params['date']
    days = params['days']
    limit = int(params.get('limit', 20))
    limit = max(1, min(limit, 50))

    events = []

    # Simple lunar phase markers per day (snapshot at 00:00 UTC)
    ts = get_timescale()
    for i in range(days):
        d = (date + timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        from .services.skyfield_client import calculate_moon_phase
        info = calculate_moon_phase(ts.from_datetime(d))
        events.append({
            'type': 'moon_phase',
            'date_utc': d.isoformat().replace('+00:00', 'Z') if d.tzinfo else d.isoformat(),
            'phase': info['phase_name'],
            'illumination_percent': info['illumination_percent']
        })

    total = len(events)
    truncated = total > limit
    if truncated:
        events = events[:limit]

    return {
        'success': True,
        'operation': 'celestial_events',
        'event_count': len(events),
        'total_count': total,
        'truncated': truncated,
        'events': events
    }


def visible_planets_operation(params: dict) -> dict:
    latitude = params['latitude']
    longitude = params['longitude']
    elevation = params['elevation']
    date = params['date']

    eph = get_ephemeris()
    ts = get_timescale()

    t = ts.from_datetime(date.replace(hour=DEFAULT_HOUR_UTC, minute=0, second=0, microsecond=0))
    observer = create_observer(latitude, longitude, elevation)

    planets = ['mercury', 'venus', 'mars', 'jupiter', 'saturn']
    results = []

    earth = eph['earth']
    for name in planets:
        body = get_body(name)
        astrometric = (earth + observer).at(t).observe(body).apparent()
        alt, az, _ = astrometric.altaz()
        alt_deg = float(alt.degrees)
        az_deg = float(az.degrees)
        results.append({
            'body': name,
            'altitude_degrees': alt_deg,
            'azimuth_degrees': az_deg,
            'direction': degrees_to_cardinal(az_deg),
            'is_visible': bool(alt_deg > 0.0)
        })

    visible = [r for r in results if r['is_visible']]

    return {
        'success': True,
        'operation': 'visible_planets',
        'observer': {
            'latitude': latitude,
            'longitude': longitude,
            'elevation_m': elevation,
            'time_utc': t.utc_iso(),
        },
        'count': len(visible),
        'planets': visible,
        'note': 'Visibility snapshot at 21:00 UTC'
    }


def iss_position_operation(params: dict) -> dict:
    """Placeholder: ISS tracking requires TLE data updates (network access).
    To keep server offline-friendly, we return a clear message.
    """
    return {
        'success': False,
        'operation': 'iss_position',
        'error': 'ISS tracking requires up-to-date TLE data (network). Feature not available in offline mode.',
        'action': 'Provide TLE URLs and allow network in services to enable.'
    }
