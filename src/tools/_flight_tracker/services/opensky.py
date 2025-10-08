"""OpenSky Network API client."""
from __future__ import annotations
from typing import Dict, Any
import requests


OPENSKY_API_URL = "https://opensky-network.org/api/states/all"
DEFAULT_TIMEOUT = 30


def fetch_flights_in_bbox(
    lamin: float,
    lomin: float,
    lamax: float,
    lomax: float,
    timeout: int = DEFAULT_TIMEOUT
) -> Dict[str, Any]:
    """Fetch flights in bounding box from OpenSky API.
    
    Args:
        lamin: Minimum latitude
        lomin: Minimum longitude
        lamax: Maximum latitude
        lomax: Maximum longitude
        timeout: Request timeout in seconds
        
    Returns:
        API response with states or error
    """
    params = {
        "lamin": str(lamin),
        "lomin": str(lomin),
        "lamax": str(lamax),
        "lomax": str(lomax)
    }
    
    try:
        response = requests.get(
            OPENSKY_API_URL,
            params=params,
            timeout=timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "time": data.get("time"),
                "states": data.get("states") or []
            }
        elif response.status_code == 404:
            return {
                "success": True,
                "states": []
            }
        else:
            return {
                "success": False,
                "error": f"OpenSky API error {response.status_code}: {response.text}"
            }
    
    except requests.Timeout:
        return {
            "success": False,
            "error": f"OpenSky API timeout after {timeout}s"
        }
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"OpenSky API request failed: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }
