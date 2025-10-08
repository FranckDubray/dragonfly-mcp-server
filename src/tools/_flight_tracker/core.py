"""Flight Tracker core logic."""
from __future__ import annotations
from typing import Dict, Any, List, Optional
import fnmatch

from .validators import validate_position, validate_radius, validate_filters
from .utils import calculate_bbox, calculate_distance, detect_flight_phase, format_flight_data
from .services.opensky import fetch_flights_in_bbox


def handle_track_flights(
    latitude: float,
    longitude: float,
    radius_km: float,
    altitude_min: Optional[float] = None,
    altitude_max: Optional[float] = None,
    on_ground_only: bool = False,
    in_flight_only: bool = False,
    speed_min: Optional[float] = None,
    speed_max: Optional[float] = None,
    countries: Optional[List[str]] = None,
    callsign_pattern: Optional[str] = None,
    max_results: int = 100,
    sort_by: str = "distance",
    include_metadata: bool = True
) -> Dict[str, Any]:
    """Handle track_flights operation.
    
    Args:
        latitude: Center latitude
        longitude: Center longitude
        radius_km: Search radius in km
        altitude_min: Min altitude filter (meters)
        altitude_max: Max altitude filter (meters)
        on_ground_only: Only ground aircraft
        in_flight_only: Only flying aircraft
        speed_min: Min speed filter (km/h)
        speed_max: Max speed filter (km/h)
        countries: Country filter list
        callsign_pattern: Callsign pattern (e.g., "AFR*")
        max_results: Max results limit
        sort_by: Sort field
        include_metaInclude flight phase analysis
        
    Returns:
        Tracking results
    """
    # Validate position
    pos_result = validate_position(latitude, longitude)
    if not pos_result["valid"]:
        return {"error": pos_result["error"]}
    
    # Validate radius
    radius_result = validate_radius(radius_km)
    if not radius_result["valid"]:
        return {"error": radius_result["error"]}
    
    # Validate filters
    filters_result = validate_filters(
        altitude_min=altitude_min,
        altitude_max=altitude_max,
        speed_min=speed_min,
        speed_max=speed_max,
        on_ground_only=on_ground_only,
        in_flight_only=in_flight_only
    )
    if not filters_result["valid"]:
        return {"error": filters_result["error"]}
    
    # Calculate bounding box
    bbox = calculate_bbox(latitude, longitude, radius_km)
    
    # Fetch flights from OpenSky API
    fetch_result = fetch_flights_in_bbox(
        lamin=bbox["lamin"],
        lomin=bbox["lomin"],
        lamax=bbox["lamax"],
        lomax=bbox["lomax"]
    )
    
    if not fetch_result["success"]:
        return {"error": fetch_result["error"]}
    
    raw_flights = fetch_result.get("states", [])
    if not raw_flights:
        return {
            "success": True,
            "center": {"latitude": latitude, "longitude": longitude},
            "radius_km": radius_km,
            "filters_applied": _build_filters_summary(
                altitude_min, altitude_max, on_ground_only, in_flight_only,
                speed_min, speed_max, countries, callsign_pattern
            ),
            "flights_count": 0,
            "flights": []
        }
    
    # Process and filter flights
    processed_flights = []
    
    for raw_flight in raw_flights:
        # Parse raw flight data (OpenSky format)
        flight = _parse_opensky_flight(raw_flight)
        if not flight:
            continue
        
        # Calculate distance from center
        distance_km = calculate_distance(
            latitude, longitude,
            flight["position"]["latitude"], flight["position"]["longitude"]
        )
        
        # Skip if outside radius (API bbox is rectangular, we want circular)
        if distance_km > radius_km:
            continue
        
        flight["distance_km"] = round(distance_km, 2)
        
        # Apply filters
        if not _apply_filters(
            flight,
            altitude_min=altitude_min,
            altitude_max=altitude_max,
            on_ground_only=on_ground_only,
            in_flight_only=in_flight_only,
            speed_min=speed_min,
            speed_max=speed_max,
            countries=countries,
            callsign_pattern=callsign_pattern
        ):
            continue
        
        # Add metadata if requested
        if include_metadata:
            flight["flight_phase"] = detect_flight_phase(
                altitude_m=flight.get("altitude_m"),
                vertical_rate_ms=flight.get("vertical_rate_ms"),
                speed_kmh=flight.get("speed_kmh"),
                on_ground=flight.get("on_ground", False)
            )
        
        processed_flights.append(flight)
    
    # Sort flights
    processed_flights = _sort_flights(processed_flights, sort_by)
    
    # Limit results
    if len(processed_flights) > max_results:
        processed_flights = processed_flights[:max_results]
    
    return {
        "success": True,
        "center": {"latitude": latitude, "longitude": longitude},
        "radius_km": radius_km,
        "bbox": bbox,
        "filters_applied": _build_filters_summary(
            altitude_min, altitude_max, on_ground_only, in_flight_only,
            speed_min, speed_max, countries, callsign_pattern
        ),
        "flights_count": len(processed_flights),
        "flights": processed_flights
    }


def _parse_opensky_flight(raw: List) -> Optional[Dict[str, Any]]:
    """Parse OpenSky API raw flight data.
    
    OpenSky format: [icao24, callsign, origin_country, time_position, 
                     last_contact, longitude, latitude, baro_altitude, 
                     on_ground, velocity, true_track, vertical_rate, 
                     sensors, geo_altitude, squawk, spi, position_source]
    
    Args:
        raw: Raw flight array from OpenSky API
        
    Returns:
        Parsed flight dict or None if invalid
    """
    if not raw or len(raw) < 17:
        return None
    
    try:
        return {
            "icao24": raw[0],
            "callsign": (raw[1] or "").strip(),
            "country": raw[2],
            "position": {
                "latitude": raw[6],
                "longitude": raw[5]
            },
            "altitude_m": raw[7] if raw[7] is not None else None,
            "altitude_baro_m": raw[13] if raw[13] is not None else None,
            "on_ground": raw[8],
            "speed_ms": raw[9],
            "speed_kmh": round(raw[9] * 3.6, 1) if raw[9] is not None else None,
            "heading": raw[10],
            "vertical_rate_ms": raw[11],
            "squawk": raw[14],
            "last_contact": raw[4]
        }
    except (IndexError, TypeError):
        return None


def _apply_filters(
    flight: Dict[str, Any],
    altitude_min: Optional[float],
    altitude_max: Optional[float],
    on_ground_only: bool,
    in_flight_only: bool,
    speed_min: Optional[float],
    speed_max: Optional[float],
    countries: Optional[List[str]],
    callsign_pattern: Optional[str]
) -> bool:
    """Apply filters to flight.
    
    Args:
        flight: Flight data
        altitude_min: Min altitude
        altitude_max: Max altitude
        on_ground_only: Ground only
        in_flight_only: Flight only
        speed_min: Min speed
        speed_max: Max speed
        countries: Country list
        callsign_pattern: Callsign pattern
        
    Returns:
        True if flight passes filters
    """
    # Ground filter
    if on_ground_only and not flight.get("on_ground"):
        return False
    if in_flight_only and flight.get("on_ground"):
        return False
    
    # Altitude filter
    altitude = flight.get("altitude_m")
    if altitude is not None:
        if altitude_min is not None and altitude < altitude_min:
            return False
        if altitude_max is not None and altitude > altitude_max:
            return False
    
    # Speed filter
    speed = flight.get("speed_kmh")
    if speed is not None:
        if speed_min is not None and speed < speed_min:
            return False
        if speed_max is not None and speed > speed_max:
            return False
    
    # Country filter
    if countries:
        country = flight.get("country", "")
        if country not in countries:
            return False
    
    # Callsign pattern filter
    if callsign_pattern:
        callsign = flight.get("callsign", "")
        if not fnmatch.fnmatch(callsign, callsign_pattern):
            return False
    
    return True


def _sort_flights(flights: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
    """Sort flights by specified field.
    
    Args:
        flights: Flight list
        sort_by: Sort field
        
    Returns:
        Sorted flight list
    """
    if sort_by == "distance":
        return sorted(flights, key=lambda f: f.get("distance_km", 999999))
    elif sort_by == "altitude":
        return sorted(flights, key=lambda f: f.get("altitude_m") or 0, reverse=True)
    elif sort_by == "speed":
        return sorted(flights, key=lambda f: f.get("speed_kmh") or 0, reverse=True)
    elif sort_by == "callsign":
        return sorted(flights, key=lambda f: f.get("callsign", ""))
    
    return flights


def _build_filters_summary(
    altitude_min, altitude_max, on_ground_only, in_flight_only,
    speed_min, speed_max, countries, callsign_pattern
) -> Dict[str, Any]:
    """Build summary of applied filters.
    
    Returns:
        Filters summary dict
    """
    summary = {}
    
    if altitude_min is not None:
        summary["altitude_min"] = altitude_min
    if altitude_max is not None:
        summary["altitude_max"] = altitude_max
    if on_ground_only:
        summary["on_ground_only"] = True
    if in_flight_only:
        summary["in_flight_only"] = True
    if speed_min is not None:
        summary["speed_min"] = speed_min
    if speed_max is not None:
        summary["speed_max"] = speed_max
    if countries:
        summary["countries"] = countries
    if callsign_pattern:
        summary["callsign_pattern"] = callsign_pattern
    
    return summary
