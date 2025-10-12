"""
Open-Meteo API client for upper air weather data.
"""
import logging
import requests

logger = logging.getLogger(__name__)

OPENMETEO_API_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT_SECONDS = 30

def get_winds_aloft(latitude, longitude, pressure_level_hpa):
    """
    Fetch wind and temperature data at specific pressure level from Open-Meteo.
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        pressure_level_hpa: Pressure level in hPa (e.g., 225 for FL360)
        
    Returns:
        dict: Weather data or error dict
    """
    logger.info(f"Fetching winds aloft: lat={latitude}, lon={longitude}, pressure={pressure_level_hpa}hPa")
    
    # Build parameter names for the requested pressure level
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'hourly': f'wind_speed_{pressure_level_hpa}hPa,wind_direction_{pressure_level_hpa}hPa,temperature_{pressure_level_hpa}hPa',
        'timezone': 'auto',
        'forecast_days': 1  # Only need current forecast
    }
    
    try:
        response = requests.get(OPENMETEO_API_URL, params=params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        
        # Extract current hour data (first value in arrays)
        hourly = data.get('hourly', {})
        
        wind_speed_key = f'wind_speed_{pressure_level_hpa}hPa'
        wind_dir_key = f'wind_direction_{pressure_level_hpa}hPa'
        temp_key = f'temperature_{pressure_level_hpa}hPa'
        
        if wind_speed_key not in hourly or wind_dir_key not in hourly:
            logger.warning(f"No data available for pressure level {pressure_level_hpa} hPa")
            return {
                "error": f"No data available for pressure level {pressure_level_hpa} hPa at this location"
            }
        
        # Get current values (index 0)
        wind_speed = hourly[wind_speed_key][0] if hourly[wind_speed_key] else None
        wind_direction = hourly[wind_dir_key][0] if hourly[wind_dir_key] else None
        temperature = hourly[temp_key][0] if temp_key in hourly and hourly[temp_key] else None
        
        # Get timestamp
        timestamp = hourly.get('time', [None])[0]
        
        logger.info(f"Open-Meteo success: wind {wind_speed} km/h @ {pressure_level_hpa}hPa")
        
        return {
            'success': True,
            'wind_speed_kmh': wind_speed,
            'wind_direction': wind_direction,
            'temperature_c': temperature,
            'pressure_level_hpa': pressure_level_hpa,
            'timestamp': timestamp,
            'timezone': data.get('timezone'),
            'source': 'Open-Meteo API'
        }
        
    except requests.exceptions.Timeout:
        logger.error(f"Request timeout after {TIMEOUT_SECONDS}s")
        return {"error": f"Request to Open-Meteo API timed out after {TIMEOUT_SECONDS}s"}
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        return {"error": f"Failed to fetch data from Open-Meteo API: {str(e)}"}
    except (KeyError, IndexError, ValueError) as e:
        logger.error(f"Response parsing failed: {str(e)}")
        return {"error": f"Failed to parse Open-Meteo API response: {str(e)}"}
