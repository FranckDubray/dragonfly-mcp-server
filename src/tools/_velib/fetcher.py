"""HTTP fetcher for Vélib' Open Data API."""
from __future__ import annotations
from typing import Dict, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)

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
        
        logger.info(f"Fetching station information from {STATION_INFO_URL}")
        
        response = requests.get(
            STATION_INFO_URL,
            timeout=DEFAULT_TIMEOUT,
            headers={"User-Agent": "Dragonfly-MCP-Velib/1.0"}
        )
        
        if response.status_code != 200:
            logger.error(f"HTTP {response.status_code} from station info API")
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
            logger.error("Unexpected API response format (no 'stations' key)")
            return {
                "success": False,
                "error": "Unexpected API response format (no 'stations' key found)"
            }
        
        logger.info(f"Fetched {len(stations)} stations from API")
        
        return {
            "success": True,
            "data": stations,
            "count": len(stations)
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch station information: {str(e)}")
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
        
        logger.info(f"Fetching station status from {STATION_STATUS_URL}" + (f" for station {station_code}" if station_code else " (all stations)"))
        
        response = requests.get(
            STATION_STATUS_URL,
            timeout=DEFAULT_TIMEOUT,
            headers={"User-Agent": "Dragonfly-MCP-Velib/1.0"}
        )
        
        if response.status_code != 200:
            logger.error(f"HTTP {response.status_code} from station status API")
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
            logger.error("Unexpected API response format (no 'stations' key)")
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
                logger.warning(f"Station code '{station_code}' not found in real-time data ({len(stations)} stations checked)")
                return {
                    "success": False,
                    "error": f"Station code '{station_code}' not found in real-time data"
                }
            
            logger.info(f"Found station {station_code} in API response")
            return {
                "success": True,
                "data": matching[0]
            }
        
        logger.info(f"Fetched {len(stations)} station statuses from API")
        
        return {
            "success": True,
            "data": stations,
            "count": len(stations)
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch station status: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to fetch station status: {str(e)}"
        }
