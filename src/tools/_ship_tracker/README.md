# Ship Tracker Tool

Track ships and vessels in real-time using AIS (Automatic Identification System) data.

## Features

- **Track ships in area**: Find all vessels within a radius of any location
- **Get ship details**: Retrieve detailed information about a specific vessel by MMSI
- **Check port traffic**: Monitor shipping activity near major ports
- **Free API**: Uses public AIS data, no API key required
- **Rich filters**: Ship type, size, speed, navigation status

## Operations

### track_ships

Find ships in a geographic area with advanced filtering.

**Parameters:**
- `latitude` (required): Center latitude (-90 to 90)
- `longitude` (required): Center longitude (-180 to 180)
- `radius_km` (optional): Search radius in km (1-500, default: 50)
- `ship_type` (optional): Filter by type (cargo, tanker, passenger, fishing, etc.)
- `min_length` (optional): Minimum ship length in meters
- `max_length` (optional): Maximum ship length in meters
- `min_speed_knots` (optional): Minimum speed in knots
- `max_speed_knots` (optional): Maximum speed in knots
- `navigation_status` (optional): Filter by status (underway, anchored, moored, etc.)
- `max_results` (optional): Maximum results (1-200, default: 50)
- `sort_by` (optional): Sort by distance/speed/length (default: distance)

**Example:**
```json
{
  "operation": "track_ships",
  "latitude": 51.9225,
  "longitude": 4.4792,
  "radius_km": 50,
  "ship_type": "cargo",
  "min_length": 200,
  "max_results": 10
}
```

**Returns:**
```json
{
  "success": true,
  "search_center": {
    "latitude": 51.9225,
    "longitude": 4.4792,
    "formatted": "51.9225°N, 4.4792°E"
  },
  "radius_km": 50,
  "ships_found": 5,
  "ships": [
    {
      "mmsi": 123456789,
      "name": "EXAMPLE SHIP",
      "ship_type": "Cargo",
      "ship_type_code": 70,
      "position": {
        "latitude": 51.9325,
        "longitude": 4.4892,
        "formatted": "51.9325°N, 4.4892°E"
      },
      "distance_km": 1.5,
      "speed": {
        "knots": 12.5,
        "kmh": 23.2
      },
      "heading": 45,
      "course": 45,
      "navigation_status": "Under way using engine",
      "destination": "ROTTERDAM",
      "eta": "01-10 14:00",
      "dimensions": {
        "length_m": 200,
        "length_ft": 656.2,
        "width_m": 32,
        "draught_m": 8.5
      },
      "timestamp": "2025-01-09T12:00:00Z"
    }
  ],
  "filters_applied": {
    "ship_type": "cargo",
    "min_length_m": 200
  }
}
```

### get_ship_details

Get detailed information about a specific ship by its MMSI number.

**Parameters:**
- `mmsi` (required): Maritime Mobile Service Identity (9-digit number)

**Example:**
```json
{
  "operation": "get_ship_details",
  "mmsi": 123456789
}
```

**Returns:**
```json
{
  "success": true,
  "mmsi": 123456789,
  "name": "EXAMPLE VESSEL",
  "imo": 1234567,
  "callsign": "EXAM1",
  "ship_type": "Cargo",
  "ship_type_code": 70,
  "country": "Netherlands",
  "position": {
    "latitude": 51.9225,
    "longitude": 4.4792,
    "formatted": "51.9225°N, 4.4792°E"
  },
  "speed": {
    "knots": 10.0,
    "kmh": 18.5
  },
  "heading": 90,
  "course": 90,
  "navigation_status": "Under way using engine",
  "destination": "HAMBURG",
  "eta": "01-10 08:00",
  "dimensions": {
    "length_m": 180,
    "length_ft": 590.6,
    "width_m": 28,
    "draught_m": 7.5
  },
  "timestamp": "2025-01-09T12:00:00Z",
  "last_position_update": "2025-01-09T11:55:00Z"
}
```

### get_port_traffic

Monitor shipping activity near a major port.

**Parameters:**
- `port_name` (optional): Major port name (e.g., "Rotterdam", "Singapore")
- `latitude` (optional): Port latitude (if port_name not provided)
- `longitude` (optional): Port longitude (if port_name not provided)
- `radius_km` (optional): Search radius in km (1-100, default: 10)
- `max_results` (optional): Maximum results (default: 50)

**Supported Ports:**
- Rotterdam, Singapore, Shanghai, Antwerp, Hamburg
- Los Angeles, Long Beach, New York
- Marseille, Le Havre, London
- Hong Kong, Dubai

**Example:**
```json
{
  "operation": "get_port_traffic",
  "port_name": "Rotterdam",
  "radius_km": 20,
  "max_results": 20
}
```

**Returns:**
```json
{
  "success": true,
  "port": {
    "name": "Rotterdam",
    "country": "Netherlands"
  },
  "search_center": {
    "latitude": 51.9225,
    "longitude": 4.4792,
    "formatted": "51.9225°N, 4.4792°E"
  },
  "radius_km": 20,
  "ships_found": 15,
  "traffic_summary": {
    "total_ships": 15,
    "anchored": 5,
    "underway": 8,
    "moored": 2
  },
  "ships": [...]
}
```

## Ship Types

AIS ship type categories:
- **fishing**: Fishing vessels
- **towing**: Towing vessels
- **dredging**: Dredging or underwater operations
- **diving**: Diving operations
- **military**: Military operations
- **sailing**: Sailing vessels
- **pleasure**: Pleasure craft
- **highspeed**: High speed craft
- **pilot**: Pilot vessels
- **sar**: Search and rescue vessels
- **tug**: Tugs
- **port**: Port tenders
- **pollution**: Anti-pollution equipment
- **law**: Law enforcement
- **medical**: Medical transport
- **passenger**: Passenger ships
- **cargo**: Cargo ships
- **tanker**: Tankers
- **other**: Other types

## Navigation Statuses

- **underway**: Under way using engine
- **anchored**: At anchor
- **moored**: Moored
- **aground**: Aground
- **fishing**: Engaged in fishing
- **sailing**: Under way sailing

## Use Cases

### Maritime Traffic Analysis
```bash
# Check busy shipping lanes
{
  "operation": "track_ships",
  "latitude": 51.5,
  "longitude": 1.5,
  "radius_km": 100,
  "min_speed_knots": 5
}
```

### Port Monitoring
```bash
# Monitor Rotterdam port activity
{
  "operation": "get_port_traffic",
  "port_name": "Rotterdam",
  "radius_km": 30
}
```

### Ship Tracking
```bash
# Follow a specific vessel
{
  "operation": "get_ship_details",
  "mmsi": 244123456
}
```

### Fishing Fleet Monitoring
```bash
# Track fishing vessels
{
  "operation": "track_ships",
  "latitude": 48.0,
  "longitude": -5.0,
  "radius_km": 50,
  "ship_type": "fishing"
}
```

### Large Vessel Tracking
```bash
# Track large cargo ships
{
  "operation": "track_ships",
  "latitude": 1.29,
  "longitude": 103.85,
  "radius_km": 50,
  "ship_type": "cargo",
  "min_length": 300
}
```

## Architecture

```
_ship_tracker/
  __init__.py           # Export spec()
  api.py                # Route operations to handlers
  core.py               # Business logic (track, details, port traffic)
  validators.py         # Input validation
  utils.py              # Helpers (distance calc, conversions, type names)
  services/
    aisstream.py        # AIS data client (aisstream.io integration)
```

## Data Source

Currently uses mock data for demonstration. In production, integrate with:
- **aisstream.io** (recommended): Free WebSocket and REST API
- **AISHub**: Free with AIS feed contribution
- **VesselFinder API**: Limited free tier
- Or any other AIS data provider

## Error Handling

All operations return explicit error messages:
```json
{
  "error": "Validation error: Parameter 'latitude' must be between -90 and 90"
}
```

Common errors:
- Invalid coordinates
- MMSI not found
- Port name not recognized
- Invalid ship type or navigation status

## Security

- ✅ No API key required (public AIS data)
- ✅ Input validation (coordinates, ranges, filters)
- ✅ No personal data stored
- ✅ Read-only operations (no data modification)

## Dependencies

- `requests`: HTTP client for API calls

## Future Enhancements

- WebSocket streaming for real-time updates
- Historical track playback
- Ship route prediction
- Port arrival/departure notifications
- Weather overlay integration
- Integration with real AIS data provider

## Links

- [AISStream.io Documentation](https://aisstream.io/documentation)
- [AIS Message Types](https://gpsd.gitlab.io/gpsd/AIVDM.html)
- [Ship Type Codes](https://api.vesselfinder.com/docs/ref-aistypes.html)
