"""AISStream.io WebSocket client for real-time ship tracking.

Official API: https://aisstream.io/documentation
WebSocket endpoint: wss://stream.aisstream.io/v0/stream
"""

import os
import json
import time
import math
import threading
import logging
import websocket
from typing import Dict, Any, List, Optional
from ..utils import haversine_distance

# Setup logging
logger = logging.getLogger(__name__)


class AISStreamClient:
    """Client for AISStream.io WebSocket API."""
    
    WS_URL = "wss://stream.aisstream.io/v0/stream"
    MAX_SHIPS_TO_COLLECT = 500  # Internal safety limit
    
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
        timeout: int = 15
    ) -> List[Dict[str, Any]]:
        """Get ships in a geographic area via WebSocket.
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Radius in kilometers
            max_results: Maximum number of ships to return
            timeout: WebSocket collection timeout in seconds (default: 15)
            
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
        collection_stopped = False  # Flag to stop collection when limit reached
        
        def on_message(ws, message):
            """Handle incoming AIS message."""
            nonlocal collection_stopped
            
            # Stop collecting if we hit internal limit
            if len(ships_by_mmsi) >= self.MAX_SHIPS_TO_COLLECT:
                if not collection_stopped:
                    logger.warning(f"Hit internal collection limit ({self.MAX_SHIPS_TO_COLLECT} ships), stopping early")
                    collection_stopped = True
                    ws.close()
                return
            
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
                logger.debug(f"Error parsing AIS message: {e}")
        
        def on_error(ws, error):
            """Handle WebSocket errors."""
            logger.debug(f"WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            """Handle WebSocket close."""
            logger.debug(f"WebSocket closed: {close_status_code} - {close_msg}")
        
        def on_open(ws):
            """Send subscription message on connection open."""
            subscribe_message = {
                "APIKey": self.api_key,
                "BoundingBoxes": [bbox],
                "FilterMessageTypes": ["PositionReport"]  # Only position updates
            }
            ws.send(json.dumps(subscribe_message))
            logger.debug(f"WebSocket opened, subscribed to bbox: {bbox}")
        
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
        
        # Wait for timeout (or early stop if collection_stopped)
        time.sleep(timeout)
        
        # Close connection
        ws.close()
        wst.join(timeout=1)
        
        logger.info(f"Collected {len(ships_by_mmsi)} ships in {timeout}s (limit: {self.MAX_SHIPS_TO_COLLECT})")
        
        # Convert dict to list and sort by distance
        ships = list(ships_by_mmsi.values())
        ships.sort(key=lambda s: s["distance_km"])
        
        return ships[:max_results]
    
    def get_ship_by_mmsi(self, mmsi: int, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Get ship details by MMSI number.
        
        NOTE: This operation listens to the GLOBAL AIS stream (no bounding box filter)
        which is inefficient. Recommended timeout: 30-60s for better chances.
        
        Args:
            mmsi: Maritime Mobile Service Identity number
            timeout: WebSocket collection timeout in seconds (default: 30)
            
        Returns:
            Ship details or None if not found
        """
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
                        
                        logger.info(f"Found ship MMSI {mmsi}")
                        # Close immediately when found
                        ws.close()
            except Exception as e:
                logger.debug(f"Error in get_ship_by_mmsi: {e}")
        
        def on_open(ws):
            subscribe_message = {
                "APIKey": self.api_key,
                "FilterMessageTypes": ["PositionReport"]
                # NOTE: No BoundingBoxes = global stream (inefficient but necessary)
            }
            ws.send(json.dumps(subscribe_message))
            logger.debug(f"WebSocket opened, listening globally for MMSI {mmsi}")
        
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
        
        if ship_found:
            logger.info(f"Ship MMSI {mmsi} found after listening for {timeout}s")
        else:
            logger.warning(f"Ship MMSI {mmsi} not found after {timeout}s (try longer timeout)")
        
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
