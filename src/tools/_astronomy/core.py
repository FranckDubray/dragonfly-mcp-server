"""
Core astronomy calculation logic
"""

from .services.skyfield_client import (
    get_timescale, get_ephemeris, get_body, create_observer,
    calculate_moon_phase
)
from .constants import PLANET_DATA, BRIGHT_STARS
from .utils import (
    format_position, format_time, calculate_visibility,
    format_physical_data, degrees_to_cardinal
)
from datetime import timedelta


def planet_position(params):
    """Calculate planet position for observer"""
    body_name = params['body']
    latitude = params['latitude']
    longitude = params['longitude']
    elevation = params.get('elevation', 0)
    date = params['date']
    
    ts = get_timescale()
    eph = get_ephemeris()
    
    # Create observer
    observer_loc = create_observer(latitude, longitude, elevation)
    earth = eph['earth']
    observer = earth + observer_loc
    
    # Get body
    body = get_body(body_name)
    
    # Create time
    t = ts.utc(date.year, date.month, date.day, date.hour, date.minute, date.second)
    
    # Calculate position
    astrometric = observer.at(t).observe(body)
    position_data = format_position(astrometric, t)
    
    return {
        'success': True,
        'operation': 'planet_position',
        'body': body_name,
        'observer': {
            'latitude': latitude,
            'longitude': longitude,
            'elevation_m': elevation
        },
        'observation_time': date.isoformat(),
        'position': position_data,
        'visibility_status': calculate_visibility(position_data['horizontal']['altitude']['degrees'])
    }


def moon_phase_operation(params):
    """Calculate current moon phase"""
    date = params['date']
    
    ts = get_timescale()
    t = ts.utc(date.year, date.month, date.day, date.hour, date.minute, date.second)
    
    phase_info = calculate_moon_phase(t)
    
    return {
        'success': True,
        'operation': 'moon_phase',
        'observation_time': date.isoformat(),
        'phase': phase_info
    }


def sun_moon_times_operation(params):
    """Calculate sunrise, sunset, moonrise, moonset times"""
    latitude = params['latitude']
    longitude = params['longitude']
    elevation = params.get('elevation', 0)
    date = params['date']
    
    ts = get_timescale()
    eph = get_ephemeris()
    
    observer_loc = create_observer(latitude, longitude, elevation)
    
    # Create time range (24 hours)
    t0 = ts.utc(date.year, date.month, date.day, 0, 0, 0)
    t1 = ts.utc(date.year, date.month, date.day, 23, 59, 59)
    
    # Calculate sun rise/set
    from skyfield import almanac
    
    # sunrise_sunset expects topos, not earth+topos
    f = almanac.sunrise_sunset(eph, observer_loc)
    times, events = almanac.find_discrete(t0, t1, f)
    
    sun_rise = None
    sun_set = None
    for t, e in zip(times, events):
        if e:  # Rise
            sun_rise = format_time(t)
        else:  # Set
            sun_set = format_time(t)
    
    # Calculate moon rise/set
    earth = eph['earth']
    observer = earth + observer_loc
    moon = eph['moon']
    
    # Find when moon is above horizon
    def moon_above_horizon(t):
        astrometric = observer.at(t).observe(moon)
        alt, _, _ = astrometric.apparent().altaz()
        return alt.degrees > 0
    
    # Simple rise/set detection
    moon_rise = None
    moon_set = None
    
    # Sample every hour to find rise/set
    current = t0
    was_up = moon_above_horizon(current)
    
    for hour in range(24):
        current = ts.utc(date.year, date.month, date.day, hour, 0, 0)
        is_up = moon_above_horizon(current)
        
        if is_up and not was_up:
            moon_rise = format_time(current)
        elif not is_up and was_up:
            moon_set = format_time(current)
        
        was_up = is_up
    
    return {
        'success': True,
        'operation': 'sun_moon_times',
        'date': date.date().isoformat(),
        'observer': {
            'latitude': latitude,
            'longitude': longitude,
            'elevation_m': elevation
        },
        'sun': {
            'rise': sun_rise,
            'set': sun_set
        },
        'moon': {
            'rise': moon_rise,
            'set': moon_set
        },
        'note': 'Times are in UTC'
    }


def celestial_events_operation(params):
    """Find celestial events (moon phases, eclipses) in date range"""
    date = params['date']
    days = params.get('days', 7)
    
    ts = get_timescale()
    eph = get_ephemeris()
    
    # Date range
    t0 = ts.utc(date.year, date.month, date.day, 0, 0, 0)
    end_date = date + timedelta(days=days)
    t1 = ts.utc(end_date.year, end_date.month, end_date.day, 23, 59, 59)
    
    # Find moon phases
    from skyfield import almanac
    
    phases_func = almanac.moon_phases(eph)
    times, phases = almanac.find_discrete(t0, t1, phases_func)
    
    phase_names = ['New Moon', 'First Quarter', 'Full Moon', 'Last Quarter']
    
    events = []
    for t, phase in zip(times, phases):
        events.append({
            'type': 'moon_phase',
            'phase': phase_names[phase],
            'time': format_time(t)
        })
    
    return {
        'success': True,
        'operation': 'celestial_events',
        'date_range': {
            'start': date.date().isoformat(),
            'end': end_date.date().isoformat(),
            'days': days
        },
        'events': events,
        'event_count': len(events),
        'note': 'Times are in UTC. Currently showing moon phases only.'
    }


def planet_info_operation(params):
    """Get physical characteristics of a planet"""
    body_name = params['body']
    
    if body_name not in PLANET_DATA:
        return {
            'success': False,
            'error': f"No data available for body: {body_name}"
        }
    
    data = PLANET_DATA[body_name]
    formatted = format_physical_data(data)
    
    return {
        'success': True,
        'operation': 'planet_info',
        'body': body_name,
        'data': formatted,
        'source': 'NASA Planetary Fact Sheets'
    }


def visible_planets_operation(params):
    """Find visible planets for tonight"""
    latitude = params['latitude']
    longitude = params['longitude']
    elevation = params.get('elevation', 0)
    date = params['date']
    
    ts = get_timescale()
    eph = get_ephemeris()
    
    observer_loc = create_observer(latitude, longitude, elevation)
    earth = eph['earth']
    observer = earth + observer_loc
    
    # Check at 21:00 local time (simplified - using UTC)
    t = ts.utc(date.year, date.month, date.day, 21, 0, 0)
    
    planets = ['mercury', 'venus', 'mars', 'jupiter', 'saturn']
    visible = []
    
    for planet_name in planets:
        body = get_body(planet_name)
        astrometric = observer.at(t).observe(body)
        position = format_position(astrometric, t)
        
        alt = position['horizontal']['altitude']['degrees']
        az = position['horizontal']['azimuth']['degrees']
        
        if alt > 0:
            visible.append({
                'planet': planet_name,
                'altitude_degrees': alt,
                'azimuth_degrees': az,
                'direction': degrees_to_cardinal(az),
                'visibility': calculate_visibility(alt),
                'brightness': get_planet_brightness(planet_name)
            })
    
    # Sort by altitude (highest first)
    visible.sort(key=lambda x: x['altitude_degrees'], reverse=True)
    
    return {
        'success': True,
        'operation': 'visible_planets',
        'observation_time': t.utc_iso(),
        'observer': {
            'latitude': latitude,
            'longitude': longitude,
            'elevation_m': elevation
        },
        'visible_planets': visible,
        'count': len(visible),
        'note': 'Visibility calculated for 21:00 UTC. Actual visibility depends on weather and light pollution.'
    }


def iss_position_operation(params):
    """Get International Space Station position"""
    latitude = params.get('latitude')
    longitude = params.get('longitude')
    elevation = params.get('elevation', 0)
    date = params['date']
    
    # Note: ISS tracking requires TLE data which needs to be loaded separately
    # This is a placeholder implementation
    
    return {
        'success': False,
        'operation': 'iss_position',
        'error': 'ISS tracking not yet implemented. Requires TLE (Two-Line Element) data loading.',
        'note': 'ISS tracking will be added in future updates using satellite TLE data from CelesTrak or Space-Track.'
    }


def star_position_operation(params):
    """Get star position"""
    star_name = params['star_name']
    latitude = params['latitude']
    longitude = params['longitude']
    elevation = params.get('elevation', 0)
    date = params['date']
    
    star_name_lower = star_name.lower().strip()
    
    if star_name_lower not in BRIGHT_STARS:
        available = ', '.join(sorted(BRIGHT_STARS.keys()))
        return {
            'success': False,
            'error': f"Star '{star_name}' not found in catalog.",
            'available_stars': available
        }
    
    star_info = BRIGHT_STARS[star_name_lower]
    
    # Note: Full implementation would use Hipparcos catalog
    # This is a simplified version
    
    return {
        'success': False,
        'operation': 'star_position',
        'error': 'Star position calculation not yet fully implemented.',
        'note': f"Star '{star_info['name']}' is in constellation {star_info['constellation']} with magnitude {star_info['magnitude']}. Full positional calculations will be added in future updates using Hipparcos catalog."
    }


def get_planet_brightness(planet_name):
    """Get approximate brightness/magnitude for planet"""
    # Approximate typical magnitudes
    magnitudes = {
        'mercury': 0.0,
        'venus': -4.0,
        'mars': 0.5,
        'jupiter': -2.5,
        'saturn': 0.5
    }
    return magnitudes.get(planet_name, 0)
