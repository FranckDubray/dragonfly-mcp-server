"""AISStream API client for ship tracking.

Free, public AIS data from aisstream.io
Documentation: https://aisstream.io/documentation
"""

import requests
from typing import Dict, Any, List, Optional
from ..utils import haversine_distance, knots_to_kmh


class AISStreamClient:
    """Client for AISStream API."""
    
    # Using public AIS data aggregators as fallback
    # Note: aisstream.io primarily uses WebSocket, but we can use REST endpoints
    BASE_URL = "https://api.vesselfinder.com/pro/ais"
    
    def __init__(self):
        """Initialize AIS client.
        
        Note: This uses public AIS data. No API key required for basic usage.
        """
        pass
    
    def get_ships_in_area(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """Get ships in a geographic area.
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Radius in kilometers
            max_results: Maximum number of ships to return
            
        Returns:
            List of ships with AIS data
            
        Note:
            This is a simplified implementation using mock data for demonstration.
            In production, integrate with aisstream.io WebSocket API or
            a proper AIS data provider.
        """
        # For now, return mock data structure
        # In production, this would call actual AIS API
        ships = []
        
        # Mock implementation - replace with actual API calls
        # Example ship data structure based on AIS standard
        mock_ship = {
            "mmsi": 123456789,
            "name": "EXAMPLE SHIP",
            "ship_type": 70,  # Cargo
            "latitude": latitude + 0.01,
            "longitude": longitude + 0.01,
            "speed": 12.5,  # knots
            "heading": 45,  # degrees
            "course": 45,  # degrees
            "navigation_status": 0,  # Underway using engine
            "destination": "PORT OF EXAMPLE",
            "eta": "12-25 14:00",
            "length": 200,  # meters
            "width": 32,  # meters
            "draught": 8.5,  # meters
            "timestamp": "2025-01-09T12:00:00Z"
        }
        
        # Calculate distance
        distance = haversine_distance(
            latitude, longitude,
            mock_ship["latitude"], mock_ship["longitude"]
        )
        
        if distance <= radius_km:
            mock_ship["distance_km"] = round(distance, 2)
            ships.append(mock_ship)
        
        return ships[:max_results]
    
    def get_ship_by_mmsi(self, mmsi: int) -> Optional[Dict[str, Any]]:
        """Get ship details by MMSI number.
        
        Args:
            mmsi: Maritime Mobile Service Identity number
            
        Returns:
            Ship details or None if not found
        """
        # Mock implementation
        return {
            "mmsi": mmsi,
            "name": "EXAMPLE VESSEL",
            "ship_type": 70,
            "latitude": 48.8566,
            "longitude": 2.3522,
            "speed": 10.0,
            "heading": 90,
            "course": 90,
            "navigation_status": 0,
            "destination": "EXAMPLE PORT",
            "eta": "01-10 08:00",
            "imo": 1234567,
            "callsign": "EXAM1",
            "length": 180,
            "width": 28,
            "draught": 7.5,
            "country": "France",
            "timestamp": "2025-01-09T12:00:00Z",
            "last_position_update": "2025-01-09T11:55:00Z"
        }


# Helper function to get major ports coordinates (can be expanded)
MAJOR_PORTS = {
    "rotterdam": {"lat": 51.9225, "lon": 4.4792, "country": "Netherlands"},
    "singapore": {"lat": 1.2897, "lon": 103.8501, "country": "Singapore"},
    "shanghai": {"lat": 31.2304, "lon": 121.4737, "country": "China"},
    "antwerp": {"lat": 51.2194, "lon": 4.4025, "country": "Belgium"},
    "hamburg": {"lat": 53.5511, "lon": 9.9937, "country": "Germany"},
    "losangeles": {"lat": 33.7405, "lon": -118.2718, "country": "USA"},
    "longbeach": {"lat": 33.7683, "lon": -118.1956, "country": "USA"},
    "newyork": {"lat": 40.6895, "lon": -74.0447, "country": "USA"},
    "marseille": {"lat": 43.3614, "lon": 5.3364, "country": "France"},
    "lehavre": {"lat": 49.4938, "lon": 0.1077, "country": "France"},
    "london": {"lat": 51.5074, "lon": -0.1278, "country": "UK"},
    "hongkong": {"lat": 22.3193, "lon": 114.1694, "country": "Hong Kong"},
    "dubai": {"lat": 25.2769, "lon": 55.2963, "country": "UAE"},
}


def get_port_coordinates(port_name: str) -> Optional[Dict[str, Any]]:
    """Get coordinates for a major port by name.
    
    Args:
        port_name: Port name (case-insensitive)
        
    Returns:
        Port data with coordinates or None if not found
    """
    port_key = port_name.lower().replace(" ", "").replace("-", "")
    return MAJOR_PORTS.get(port_key)
