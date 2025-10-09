"""AISStream.io WebSocket client for real-time ship tracking.

Official API: https://aisstream.io/documentation
WebSocket endpoint: wss://stream.aisstream.io/v0/stream
"""

import os
import json
import time
import math
import threading
import websocket
from typing import Dict, Any, List, Optional
from ..utils import haversine_distance


class AISStreamClient:
    """Client for AISStream.io WebSocket API."""
    
    WS_URL = "wss://stream.aisstream.io/v0/stream"
    
    def __init__(self):
        """Initialize AIS client with API key from environment."""
        self.api_key = os.getenv("AISSTREAM_API_KEY", "").strip()
        if not self.api_key:
            raise ValueError(
                "AISSTREAM_API_KEY not found in environment variables. "
                "Get a free API key at: https://aisstream.io"
            )
    
    def get_ships_in_area(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
        max_results: int = 50,
        timeout: int = 10
    ) -> List[Dict[str, Any]]:
        """Get ships in a geographic area via WebSocket.
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Radius in kilometers
            max_results: Maximum number of ships to return
            timeout: WebSocket collection timeout in seconds (default: 10)
            
        Returns:
            List of ships with AIS data
        """
        # Calculate bounding box from center + radius
        # Rough approximation: 1 degree latitude ≈ 111 km
        lat_delta = radius_km / 111.0
        # Longitude varies with latitude
        lon_delta = radius_km / (111.0 * abs(math.cos(math.radians(latitude))))
        
        # AISStream.io format: [[lat1, lon1], [lat2, lon2]]
        # NOT [lon, lat] - it's [lat, lon] !
        bbox = [
            [latitude - lat_delta, longitude - lon_delta],  # SW corner
            [latitude + lat_delta, longitude + lon_delta]   # NE corner
        ]
        
        # Collect ships from WebSocket
        ships_by_mmsi = {}  # Deduplicate by MMSI
        
        def on_message(ws, message):
            """Handle incoming AIS message."""
            try:
                data = json.loads(message)
                
                # AISStream sends different message types
                if data.get("MessageType") == "PositionReport":
                    metadata = data.get("MetaData", {})
                    mmsi = metadata.get("MMSI")
                    
                    if not mmsi:
                        return
                    
                    # Extract position report data
                    msg = data.get("Message", {}).get("PositionReport", {})
                    
                    ship_lat = msg.get("Latitude")
                    ship_lon = msg.get("Longitude")
                    
                    if ship_lat is None or ship_lon is None:
                        return
                    
                    # Calculate distance from center
                    distance = haversine_distance(latitude, longitude, ship_lat, ship_lon)
                    
                    if distance > radius_km:
                        return
                    
                    # Build ship data
                    ship = {
                        "mmsi": mmsi,
                        "name": metadata.get("ShipName", "Unknown").strip(),
                        "ship_type": msg.get("ShipType", 0),
                        "latitude": ship_lat,
                        "longitude": ship_lon,
                        "speed": msg.get("Sog", 0),  # Speed over ground in knots
                        "heading": msg.get("TrueHeading"),
                        "course": msg.get("Cog"),  # Course over ground
                        "navigation_status": msg.get("NavigationalStatus", 15),
                        "destination": metadata.get("Destination", "Unknown").strip(),
                        "eta": metadata.get("ETA"),
                        "length": metadata.get("Dimension", {}).get("A", 0) + metadata.get("Dimension", {}).get("B", 0),
                        "width": metadata.get("Dimension", {}).get("C", 0) + metadata.get("Dimension", {}).get("D", 0),
                        "draught": msg.get("Draught"),
                        "callsign": metadata.get("CallSign", "").strip(),
                        "imo": metadata.get("IMO"),
                        "timestamp": metadata.get("time_utc"),
                        "distance_km": round(distance, 2)
                    }
                    
                    # Deduplicate by MMSI (keep latest)
                    ships_by_mmsi[mmsi] = ship
                    
            except Exception as e:
                # Silent fail on parse errors (don't break the stream)
                pass
        
        def on_error(ws, error):
            """Handle WebSocket errors."""
            pass  # Silent errors
        
        def on_close(ws, close_status_code, close_msg):
            """Handle WebSocket close."""
            pass
        
        def on_open(ws):
            """Send subscription message on connection open."""
            subscribe_message = {
                "APIKey": self.api_key,
                "BoundingBoxes": [bbox],
                "FilterMessageTypes": ["PositionReport"]  # Only position updates
            }
            ws.send(json.dumps(subscribe_message))
        
        # Create WebSocket connection
        ws = websocket.WebSocketApp(
            self.WS_URL,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        # Run WebSocket in a thread with timeout
        wst = threading.Thread(target=ws.run_forever)
        wst.daemon = True
        wst.start()
        
        # Wait for timeout
        time.sleep(timeout)
        
        # Close connection
        ws.close()
        wst.join(timeout=1)
        
        # Convert dict to list and sort by distance
        ships = list(ships_by_mmsi.values())
        ships.sort(key=lambda s: s["distance_km"])
        
        return ships[:max_results]
    
    def get_ship_by_mmsi(self, mmsi: int, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """Get ship details by MMSI number.
        
        Args:
            mmsi: Maritime Mobile Service Identity number
            timeout: WebSocket collection timeout in seconds
            
        Returns:
            Ship details or None if not found
        """
        # For MMSI lookup, we need to listen globally (no bbox filter)
        # This is expensive, so we use a short timeout
        
        ship_found = None
        
        def on_message(ws, message):
            nonlocal ship_found
            try:
                data = json.loads(message)
                
                if data.get("MessageType") == "PositionReport":
                    metadata = data.get("MetaData", {})
                    
                    if metadata.get("MMSI") == mmsi:
                        msg = data.get("Message", {}).get("PositionReport", {})
                        
                        ship_found = {
                            "mmsi": mmsi,
                            "name": metadata.get("ShipName", "Unknown").strip(),
                            "ship_type": msg.get("ShipType", 0),
                            "latitude": msg.get("Latitude"),
                            "longitude": msg.get("Longitude"),
                            "speed": msg.get("Sog", 0),
                            "heading": msg.get("TrueHeading"),
                            "course": msg.get("Cog"),
                            "navigation_status": msg.get("NavigationalStatus", 15),
                            "destination": metadata.get("Destination", "Unknown").strip(),
                            "eta": metadata.get("ETA"),
                            "length": metadata.get("Dimension", {}).get("A", 0) + metadata.get("Dimension", {}).get("B", 0),
                            "width": metadata.get("Dimension", {}).get("C", 0) + metadata.get("Dimension", {}).get("D", 0),
                            "draught": msg.get("Draught"),
                            "callsign": metadata.get("CallSign", "").strip(),
                            "imo": metadata.get("IMO"),
                            "timestamp": metadata.get("time_utc"),
                            "last_position_update": metadata.get("time_utc")
                        }
                        
                        # Close immediately when found
                        ws.close()
            except Exception:
                pass
        
        def on_open(ws):
            subscribe_message = {
                "APIKey": self.api_key,
                "FilterMessageTypes": ["PositionReport"]
            }
            ws.send(json.dumps(subscribe_message))
        
        ws = websocket.WebSocketApp(
            self.WS_URL,
            on_open=on_open,
            on_message=on_message
        )
        
        wst = threading.Thread(target=ws.run_forever)
        wst.daemon = True
        wst.start()
        
        # Wait for timeout or until found
        wst.join(timeout=timeout)
        ws.close()
        
        return ship_found


# Helper function: major ports coordinates
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
