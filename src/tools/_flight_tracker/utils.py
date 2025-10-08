"""Flight Tracker utilities."""
from __future__ import annotations
from typing import Dict, Any, Optional
import math


def calculate_bbox(latitude: float, longitude: float, radius_km: float) -> Dict[str, float]:
    """Calculate bounding box from center point and radius.
    
    Args:
        latitude: Center latitude
        longitude: Center longitude
        radius_km: Radius in kilometers
        
    Returns:
        Bounding box dict with lamin, lomin, lamax, lomax
    """
    # Approximate conversion (good enough for flight tracking)
    # 1 degree latitude ≈ 111 km
    # 1 degree longitude ≈ 111 km * cos(latitude)
    
    lat_rad = math.radians(latitude)
    
    delta_lat = radius_km / 111.0
    delta_lon = radius_km / (111.0 * math.cos(lat_rad))
    
    return {
        "lamin": round(latitude - delta_lat, 6),
        "lamax": round(latitude + delta_lat, 6),
        "lomin": round(longitude - delta_lon, 6),
        "lomax": round(longitude + delta_lon, 6)
    }


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula.
    
    Args:
        lat1: First point latitude
        lon1: First point longitude
        lat2: Second point latitude
        lon2: Second point longitude
        
    Returns:
        Distance in kilometers
    """
    # Earth radius in km
    R = 6371.0
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    
    return distance


def detect_flight_phase(
    altitude_m: Optional[float],
    vertical_rate_ms: Optional[float],
    speed_kmh: Optional[float],
    on_ground: bool
) -> str:
    """Detect flight phase from flight data.
    
    Args:
        altitude_m: Altitude in meters
        vertical_rate_ms: Vertical rate in m/s
        speed_kmh: Speed in km/h
        on_ground: Ground flag
        
    Returns:
        Flight phase string
    """
    if on_ground:
        if speed_kmh is not None and speed_kmh > 50:
            return "taxiing"
        return "parked"
    
    if altitude_m is None:
        return "unknown"
    
    # Very low altitude
    if altitude_m < 300:
        if vertical_rate_ms is not None and vertical_rate_ms < -2:
            return "landing_imminent"
        return "final_approach"
    
    # Low altitude
    if altitude_m < 3000:
        if vertical_rate_ms is not None:
            if vertical_rate_ms > 5:
                return "climb"
            elif vertical_rate_ms < -5:
                return "descent"
        return "approach"
    
    # Medium/high altitude
    if altitude_m < 8000:
        if vertical_rate_ms is not None:
            if vertical_rate_ms > 5:
                return "climb"
            elif vertical_rate_ms < -5:
                return "descent"
        return "intermediate"
    
    # Cruise altitude
    if vertical_rate_ms is not None and abs(vertical_rate_ms) < 2:
        return "cruise"
    elif vertical_rate_ms is not None and vertical_rate_ms > 2:
        return "climb"
    elif vertical_rate_ms is not None and vertical_rate_ms < -2:
        return "descent"
    
    return "cruise"


def format_flight_data(flight: Dict[str, Any]) -> Dict[str, Any]:
    """Format flight data for output.
    
    Args:
        flight: Raw flight data
        
    Returns:
        Formatted flight data
    """
    return {
        "callsign": flight.get("callsign", "N/A"),
        "country": flight.get("country", "Unknown"),
        "position": flight.get("position"),
        "distance_km": flight.get("distance_km"),
        "altitude_m": flight.get("altitude_m"),
        "speed_kmh": flight.get("speed_kmh"),
        "heading": flight.get("heading"),
        "vertical_rate_ms": flight.get("vertical_rate_ms"),
        "on_ground": flight.get("on_ground", False),
        "flight_phase": flight.get("flight_phase"),
        "squawk": flight.get("squawk")
    }
