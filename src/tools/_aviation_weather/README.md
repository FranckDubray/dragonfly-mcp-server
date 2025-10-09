# Aviation Weather Tool

Get upper air weather data (winds, temperature) at specific altitude and coordinates using **Open-Meteo API** (free, no API key required).

## Features

- ✅ **Free API** (Open-Meteo, no authentication)
- ✅ **Real-time wind data** at any altitude (1000-20000m)
- ✅ **True Airspeed calculation** from ground speed + wind
- ✅ **Multiple pressure levels** (1000, 925, 850, 700, 600, 500, 400, 300, 250, 225, 200, 150, 100, 70, 50, 30, 20, 10 hPa)
- ✅ **Temperature at altitude**
- ✅ **Automatic unit conversions** (km/h ↔ knots, meters ↔ feet, °C ↔ °F)

## Operations

### get_winds_aloft

Get wind speed, direction, and temperature at specific coordinates and altitude.

**Parameters:**
- `latitude` (required): Latitude in decimal degrees (-90 to 90)
- `longitude` (required): Longitude in decimal degrees (-180 to 180)
- `altitude_m` (optional): Altitude in meters (1000-20000, default 11000m ~ FL360)

**Example:**
```json
{
  "operation": "get_winds_aloft",
  "latitude": 48.59,
  "longitude": 6.27,
  "altitude_m": 11278
}
```

**Response:**
```json
{
  "success": true,
  "location": {"latitude": 48.59, "longitude": 6.27},
  "altitude": {
    "meters": 11278,
    "feet": 37000,
    "flight_level": 370,
    "pressure_level_hpa": 225
  },
  "wind": {
    "speed_kmh": 66.2,
    "speed_kts": 35.7,
    "direction": 266,
    "direction_name": "W"
  },
  "temperature": {
    "celsius": -53.5,
    "fahrenheit": -64.3
  },
  "timestamp": "2025-10-09T00:00",
  "source": "Open-Meteo API"
}
```

### calculate_tas

Calculate True Airspeed (TAS) from ground speed, heading, and wind data.

**Parameters:**
- `latitude` (required): Latitude in decimal degrees
- `longitude` (required): Longitude in decimal degrees
- `ground_speed_kmh` (required): Ground speed in km/h
- `heading` (required): Aircraft heading in degrees (0-360)
- `altitude_m` (optional): Altitude in meters (default 11000m)

**Example:**
```json
{
  "operation": "calculate_tas",
  "latitude": 48.59,
  "longitude": 6.27,
  "ground_speed_kmh": 978,
  "heading": 127,
  "altitude_m": 11278
}
```

**Response:**
```json
{
  "success": true,
  "location": {"latitude": 48.59, "longitude": 6.27},
  "altitude": {"meters": 11278, "feet": 37000, "flight_level": 370},
  "aircraft": {
    "ground_speed_kmh": 978,
    "ground_speed_kts": 528.1,
    "heading": 127,
    "true_airspeed_kmh": 912.3,
    "true_airspeed_kts": 492.6
  },
  "wind": {
    "speed_kmh": 66.2,
    "speed_kts": 35.7,
    "direction": 266,
    "direction_name": "W"
  },
  "wind_components": {
    "headwind_kmh": -42.5,
    "headwind_kts": 22.9,
    "crosswind_kmh": 8.3,
    "crosswind_kts": 4.5,
    "effect": "tailwind"
  },
  "temperature": {"celsius": -53.5, "fahrenheit": -64.3},
  "timestamp": "2025-10-09T00:00",
  "source": "Open-Meteo API"
}
```

## Use Cases

### 1. Explain aircraft speed records
```json
// Why is AIC102 flying at 978 km/h ground speed?
{
  "operation": "calculate_tas",
  "latitude": 55.79,
  "longitude": 7.07,
  "ground_speed_kmh": 978.6,
  "heading": 124,
  "altitude_m": 11278
}
// Result: TAS ~913 km/h + 66 km/h tailwind = 978 km/h ground speed
```

### 2. Flight planning
```json
// Check winds at cruise altitude for route optimization
{
  "operation": "get_winds_aloft",
  "latitude": 48.86,
  "longitude": 2.35,
  "altitude_m": 10000
}
```

### 3. Integration with flight_tracker
```python
# Enrich flight data with weather
flight = flight_tracker(lat=48.59, lon=6.27, radius=50)
weather = aviation_weather(
    operation="calculate_tas",
    latitude=flight['latitude'],
    longitude=flight['longitude'],
    ground_speed_kmh=flight['speed_kmh'],
    heading=flight['heading'],
    altitude_m=flight['altitude_m']
)
```

## Architecture

```
_aviation_weather/
  __init__.py           # Export spec()
  api.py                # Route operations to handlers
  core.py               # Main logic (get_winds_aloft, calculate_tas)
  validators.py         # Input validation
  utils.py              # Conversions (hPa, TAS, units)
  services/
    openmeteo.py        # Open-Meteo API client
```

## Altitude to Pressure Level Mapping

| Altitude | Pressure | Flight Level | Typical Use |
|----------|----------|--------------|-------------|
| 20,000m | 50 hPa | FL650 | High-altitude research |
| 16,000m | 100 hPa | FL525 | Upper stratosphere |
| 13,500m | 150 hPa | FL440 | Long-haul cruise max |
| 12,000m | 200 hPa | FL390 | Long-haul cruise |
| **11,000m** | **225 hPa** | **FL360** | **Common cruise** ⭐ |
| 10,000m | 250 hPa | FL330 | Common cruise |
| 9,000m | 300 hPa | FL300 | Medium cruise |
| 7,500m | 400 hPa | FL250 | Regional jets |
| 5,500m | 500 hPa | FL180 | Turboprops |
| 3,000m | 700 hPa | FL100 | Low altitude |
| 1,500m | 850 hPa | FL50 | Approach/departure |
| 1,000m | 925 hPa | — | Low altitude |

## Data Source

**Open-Meteo API** (https://open-meteo.com)
- Free for non-commercial use
- No API key required
- Global coverage
- Hourly forecasts
- Based on NOAA GFS, DWD ICON, and other models

## Error Handling

All operations return explicit error messages:
```json
{"error": "Latitude must be between -90 and 90 (got 95.5)"}
{"error": "Parameter 'ground_speed_kmh' is required for calculate_tas operation"}
{"error": "No data available for pressure level 225 hPa at this location"}
```

## Security

- **No secrets required** (Open-Meteo is public API)
- **Input validation** on all parameters
- **Timeout**: 30 seconds per API call
- **Rate limiting**: Handled by Open-Meteo (generous free tier)

## Performance

- **API response time**: ~200-500ms
- **Caching**: Not implemented (current weather only)
- **Concurrent requests**: Supported
