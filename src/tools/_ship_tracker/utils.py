"""Utility functions for ship tracking."""

import math
from typing import Dict, Any, List, Tuple


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula.
    
    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point
        
    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def knots_to_kmh(knots: float) -> float:
    """Convert knots to km/h.
    
    Args:
        knots: Speed in knots
        
    Returns:
        Speed in km/h
    """
    return knots * 1.852


def kmh_to_knots(kmh: float) -> float:
    """Convert km/h to knots.
    
    Args:
        kmh: Speed in km/h
        
    Returns:
        Speed in knots
    """
    return kmh / 1.852


def meters_to_feet(meters: float) -> float:
    """Convert meters to feet.
    
    Args:
        meters: Length in meters
        
    Returns:
        Length in feet
    """
    return meters * 3.28084


def get_ship_type_name(ship_type: int) -> str:
    """Get human-readable ship type name from AIS type code.
    
    Args:
        ship_type: AIS ship type code (0-99)
        
    Returns:
        Human-readable ship type name
    """
    type_ranges = {
        (20, 29): "Wing in ground",
        (30, 30): "Fishing",
        (31, 31): "Towing",
        (32, 32): "Towing (large)",
        (33, 33): "Dredging/underwater ops",
        (34, 34): "Diving ops",
        (35, 35): "Military ops",
        (36, 36): "Sailing",
        (37, 37): "Pleasure craft",
        (40, 49): "High speed craft",
        (50, 50): "Pilot vessel",
        (51, 51): "Search and rescue",
        (52, 52): "Tug",
        (53, 53): "Port tender",
        (54, 54): "Anti-pollution",
        (55, 55): "Law enforcement",
        (58, 58): "Medical transport",
        (59, 59): "Non-combatant ship",
        (60, 69): "Passenger",
        (70, 79): "Cargo",
        (80, 89): "Tanker",
        (90, 99): "Other",
    }
    
    for (min_type, max_type), name in type_ranges.items():
        if min_type <= ship_type <= max_type:
            return name
    
    return "Unknown"


def get_navigation_status_name(status: int) -> str:
    """Get human-readable navigation status from AIS status code.
    
    Args:
        status: AIS navigation status code (0-15)
        
    Returns:
        Human-readable navigation status
    """
    statuses = {
        0: "Under way using engine",
        1: "At anchor",
        2: "Not under command",
        3: "Restricted maneuverability",
        4: "Constrained by draught",
        5: "Moored",
        6: "Aground",
        7: "Engaged in fishing",
        8: "Under way sailing",
        9: "Reserved for HSC",
        10: "Reserved for WIG",
        11: "Reserved",
        12: "Reserved",
        13: "Reserved",
        14: "AIS-SART",
        15: "Not defined"
    }
    
    return statuses.get(status, "Unknown")


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate bearing from point 1 to point 2.
    
    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point
        
    Returns:
        Bearing in degrees (0-360)
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lon = math.radians(lon2 - lon1)
    
    x = math.sin(delta_lon) * math.cos(lat2_rad)
    y = (math.cos(lat1_rad) * math.sin(lat2_rad) -
         math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon))
    
    bearing = math.atan2(x, y)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    
    return bearing


def format_coordinates(lat: float, lon: float) -> str:
    """Format coordinates in a human-readable way.
    
    Args:
        lat: Latitude
        lon: Longitude
        
    Returns:
        Formatted coordinates string
    """
    lat_dir = "N" if lat >= 0 else "S"
    lon_dir = "E" if lon >= 0 else "W"
    
    return f"{abs(lat):.4f}°{lat_dir}, {abs(lon):.4f}°{lon_dir}"
