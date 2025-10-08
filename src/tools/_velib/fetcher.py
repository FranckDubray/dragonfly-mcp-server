"""HTTP fetcher for Vélib' Open Data API."""
from __future__ import annotations
from typing import Dict, Any, Optional
import os


# Open Data URLs (no authentication required)
STATION_INFO_URL = os.getenv(
    "VELIB_STATION_INFO_URL",
    "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_information.json"
)

STATION_STATUS_URL = os.getenv(
    "VELIB_STATION_STATUS_URL", 
    "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json"
)

DEFAULT_TIMEOUT = 30


def fetch_station_information() -> Dict[str, Any]:
    """Fetch static station information from Open Data API.
    
    Returns:
        Dict with 'success' (bool) and 'data' or 'error'
    """
    try:
        import requests
        
        response = requests.get(
            STATION_INFO_URL,
            timeout=DEFAULT_TIMEOUT,
            headers={"User-Agent": "Dragonfly-MCP-Velib/1.0"}
        )
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text[:200]}"
            }
        
        data = response.json()
        
        # API returns nested structure with 'data' key
        if "data" in data and "stations" in data["data"]:
            stations = data["data"]["stations"]
        elif isinstance(data, dict) and "stations" in data:
            stations = data["stations"]
        elif isinstance(data, list):
            stations = data
        else:
            return {
                "success": False,
                "error": "Unexpected API response format (no 'stations' key found)"
            }
        
        return {
            "success": True,
            "data": stations,
            "count": len(stations)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to fetch station information: {str(e)}"
        }


def fetch_station_status(station_code: Optional[str] = None) -> Dict[str, Any]:
    """Fetch real-time station status from Open Data API.
    
    Args:
        station_code: Optional specific station code to filter
        
    Returns:
        Dict with 'success' (bool) and 'data' or 'error'
    """
    try:
        import requests
        
        response = requests.get(
            STATION_STATUS_URL,
            timeout=DEFAULT_TIMEOUT,
            headers={"User-Agent": "Dragonfly-MCP-Velib/1.0"}
        )
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text[:200]}"
            }
        
        data = response.json()
        
        # API returns nested structure with 'data' key
        if "data" in data and "stations" in data["data"]:
            stations = data["data"]["stations"]
        elif isinstance(data, dict) and "stations" in data:
            stations = data["stations"]
        elif isinstance(data, list):
            stations = data
        else:
            return {
                "success": False,
                "error": "Unexpected API response format (no 'stations' key found)"
            }
        
        # Filter by station_code if provided
        if station_code:
            station_code_str = str(station_code).strip()
            matching = []
            
            # The API has TWO identifiers:
            # - station_id: large integer (system ID, e.g., 213688169)
            # - stationCode: user-facing code (string, e.g., "16107")
            # We filter on stationCode since that's what users know
            for s in stations:
                # Primary: stationCode (the code users know)
                code = str(s.get("stationCode", "")).strip()
                
                # Fallback: try other field names
                if not code:
                    code = str(s.get("station_code", "")).strip()
                if not code:
                    code = str(s.get("station_id", "")).strip()
                
                if code == station_code_str:
                    matching.append(s)
                    break
            
            if not matching:
                return {
                    "success": False,
                    "error": f"Station code '{station_code}' not found in real-time data"
                }
            
            return {
                "success": True,
                "data": matching[0]
            }
        
        return {
            "success": True,
            "data": stations,
            "count": len(stations)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to fetch station status: {str(e)}"
        }
