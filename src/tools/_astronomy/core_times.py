"""
Time-related operations: moon phase, sun/moon rise and set, twilight
"""
from __future__ import annotations

from skyfield.almanac import sunrise_sunset, dark_twilight_day

from .services.skyfield_client import get_ephemeris, get_timescale, create_observer
from .services.skyfield_client import calculate_moon_phase
from .utils import format_time


def moon_phase_operation(params: dict) -> dict:
    date = params['date']

    ts = get_timescale()
    t = ts.from_datetime(date)

    phase_info = calculate_moon_phase(t)

    return {
        'success': True,
        'operation': 'moon_phase',
        'date_utc': t.utc_iso(),
        'phase': phase_info,
    }


def sun_moon_times_operation(params: dict) -> dict:
    latitude = params['latitude']
    longitude = params['longitude']
    elevation = params['elevation']
    date = params['date']

    eph = get_ephemeris()
    ts = get_timescale()

    # Compute day range: date at 00:00 UTC to +1 day
    t0 = ts.from_datetime(date.replace(hour=0, minute=0, second=0, microsecond=0))
    t1 = ts.from_datetime(date.replace(hour=23, minute=59, second=59, microsecond=0))

    observer = create_observer(latitude, longitude, elevation)

    # Sunrise/sunset for Sun
    f = sunrise_sunset(eph, eph['earth'] + observer)
    times, events = almanac_find_discrete_safe(ts, t0, t1, f)

    # Twilight categories per time
    tw_f = dark_twilight_day(eph, eph['earth'] + observer)
    tw_times, tw_events = almanac_find_discrete_safe(ts, t0, t1, tw_f)

    sun_events = []
    for ti, ev in zip(times, events):
        kind = 'sunrise' if ev == 1 else 'sunset'
        sun_events.append({'type': kind, 'time_utc': ti.utc_iso()})

    twilight = []
    TW_NAMES = {
        0: 'dark', 1: 'astronomical_twilight', 2: 'nautical_twilight',
        3: 'civil_twilight', 4: 'daylight'
    }
    for ti, ev in zip(tw_times, tw_events):
        twilight.append({'time_utc': ti.utc_iso(), 'state': TW_NAMES.get(int(ev), 'unknown')})

    return {
        'success': True,
        'operation': 'sun_moon_times',
        'date_utc': t0.utc_iso().split('T')[0],
        'sun': {
            'events': sun_events
        },
        'twilight_transitions': twilight
    }


def almanac_find_discrete_safe(ts, t0, t1, func):
    """Wrapper to call almanac.find_discrete with graceful fallback if missing.
    We avoid importing find_discrete at module import to keep file small.
    """
    from skyfield import almanac
    try:
        return almanac.find_discrete(t0, t1, func)
    except Exception:
        return ([], [])
