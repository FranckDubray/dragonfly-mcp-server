# Ship Tracker Tool

Track ships and vessels in real-time using AIS (Automatic Identification System) data via AISStream.io WebSocket API.

## Features

- **Real-time ship tracking** via WebSocket connection to AISStream.io
- **Geographic search** with bounding box (radius around coordinates)
- **Port traffic monitoring** with major ports database
- **Ship details lookup** by MMSI number
- **Configurable timeout** to control data collection duration (3-60 seconds)
- **Advanced filtering** by ship type, size, speed, navigation status
- **Free API** (AISStream.io free tier with ~200 km coastal coverage)

## Operations

### track_ships
Find all ships in a geographic area.

**Parameters:**
- `latitude` (required): Center latitude (-90 to 90)
- `longitude` (required): Center longitude (-180 to 180)
- `radius_km` (optional): Search radius in kilometers (1-500, default: 50)
- `timeout` (optional): WebSocket collection timeout in seconds (3-60, default: 10)
- `ship_type` (optional): Filter by ship type (cargo, tanker, passenger, etc.)
- `min_length` / `max_length` (optional): Filter by ship length in meters
- `min_speed_knots` / `max_speed_knots` (optional): Filter by speed
- `navigation_status` (optional): Filter by status (underway, anchored, moored, etc.)
- `max_results` (optional): Maximum ships to return (1-200, default: 50)
- `sort_by` (optional): Sort by distance/speed/length (default: distance)

**Example:**
```json
{
  "operation": "track_ships",
  "latitude": 51.9225,
  "longitude": 4.4792,
  "radius_km": 50,
  "timeout": 15,
  "max_results": 20
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
  "timeout_seconds": 15,
  "ships_found": 10,
  "ships": [
    {
      "mmsi": 244615000,
      "name": "Rotterdam EXPRESS",
      "ship_type": "Cargo",
      "ship_type_code": 70,
      "position": {
        "latitude": 51.93,
        "longitude": 4.48,
        "formatted": "51.9300°N, 4.4800°E"
      },
      "distance_km": 2.5,
      "speed": {
        "knots": 12.5,
        "kmh": 23.2
      },
      "heading": 45,
      "course": 45,
      "navigation_status": "Under way using engine",
      "destination": "ANTWERP",
      "eta": "12-25 14:00",
      "dimensions": {
        "length_m": 200,
        "length_ft": 656.2,
        "width_m": 32,
        "draught_m": 8.5
      },
      "timestamp": "2025-10-09T02:18:45Z"
    }
  ]
}
```

### get_ship_details
Get detailed information about a specific ship by MMSI number.

**Parameters:**
- `mmsi` (required): Maritime Mobile Service Identity (9-digit number)
- `timeout` (optional): WebSocket timeout in seconds (3-60, default: 10)

**Example:**
```json
{
  "operation": "get_ship_details",
  "mmsi": 244615000,
  "timeout": 30
}
```

**Returns:**
Complete ship information including position, speed, destination, dimensions, etc.

### get_port_traffic
Get ships near a major port (by name or coordinates).

**Parameters:**
- `port_name` (optional): Port name (e.g., "Rotterdam", "Singapore", "Hamburg")
- `latitude` / `longitude` (optional): Port coordinates (if port_name not provided)
- `radius_km` (optional): Search radius in km (1-100, default: 10)
- `timeout` (optional): WebSocket timeout in seconds (3-60, default: 10)
- `max_results` (optional): Maximum ships to return (default: 50)

**Example:**
```json
{
  "operation": "get_port_traffic",
  "port_name": "singapore",
  "radius_km": 20,
  "timeout": 15
}
```

**Returns:**
Ships near the port + traffic summary (anchored, underway, moored counts).

## Configuration

**Required environment variable:**
```bash
AISSTREAM_API_KEY=your_api_key_here
```

Get a free API key at: https://aisstream.io

Add to `.env`:
```bash
# Ship Tracking (AIS)
AISSTREAM_API_KEY=your_free_api_key_from_aisstream_io
```

## AIS Data Frequency

Ships emit AIS messages at different rates:
- **Fast moving vessels** (>23 knots): every 2 seconds
- **Slow moving vessels**: every 10-30 seconds
- **Anchored/moored vessels**: every 3 minutes (180 seconds)

**Timeout recommendations:**
- Quick check: 10 seconds (default)
- Standard search: 15-30 seconds
- Comprehensive scan: 60 seconds (maximum)

Longer timeout = more ships detected but slower response.

## Major Ports Database

Built-in coordinates for major ports:
- Rotterdam (Netherlands)
- Singapore
- Shanghai (China)
- Antwerp (Belgium)
- Hamburg (Germany)
- Los Angeles, Long Beach, New York (USA)
- Marseille, Le Havre (France)
- London (UK)
- Hong Kong
- Dubai (UAE)

## Use Cases

### 1. Port Traffic Monitoring
```bash
# Ships near Rotterdam port
{
  "operation": "get_port_traffic",
  "port_name": "rotterdam",
  "radius_km": 30,
  "timeout": 20
}
```

### 2. Track Cargo Ships in Area
```bash
# Cargo ships in English Channel
{
  "operation": "track_ships",
  "latitude": 50.5,
  "longitude": 0.5,
  "radius_km": 100,
  "ship_type": "cargo",
  "timeout": 30
}
```

### 3. Find Ships by Speed
```bash
# Fast-moving vessels (>15 knots)
{
  "operation": "track_ships",
  "latitude": 1.2897,
  "longitude": 103.8501,
  "radius_km": 50,
  "min_speed_knots": 15,
  "timeout": 20
}
```

### 4. Anchored Ships Only
```bash
# Ships at anchor near Singapore
{
  "operation": "track_ships",
  "latitude": 1.2897,
  "longitude": 103.8501,
  "radius_km": 50,
  "navigation_status": "anchored",
  "timeout": 30
}
```

## Architecture

```
_ship_tracker/
  __init__.py           # Export spec()
  api.py                # Route operations to handlers
  core.py               # Core logic (filtering, enrichment)
  validators.py         # Input validation
  utils.py              # Helpers (distance, conversions, formatting)
  services/
    __init__.py         # Package marker
    aisstream.py        # WebSocket client for AISStream.io
```

## Ship Types

Supported ship type filters:
- `fishing` - Fishing vessels
- `towing` - Tugs and towing vessels
- `cargo` - Cargo ships
- `tanker` - Oil/chemical tankers
- `passenger` - Passenger ferries
- `sailing` - Sailing vessels
- `pleasure` - Pleasure craft
- `highspeed` - High-speed craft
- `pilot` - Pilot vessels
- `sar` - Search and rescue
- `military` - Military ops
- `medical` - Medical transport
- `law` - Law enforcement
- `other` - Other types

## Navigation Status

- `underway` - Under way using engine
- `anchored` - At anchor
- `moored` - Moored
- `aground` - Aground
- `fishing` - Engaged in fishing
- `sailing` - Under way sailing

## Coverage Limitations

AISStream.io free tier provides:
- **~200 km coastal coverage** (where AIS receivers are located)
- **No mid-ocean coverage** (requires satellite AIS, not included)
- **Best coverage**: Major shipping lanes, ports, coastal areas
- **Limited coverage**: Remote areas, open ocean

## Error Handling

All errors return explicit messages:
```json
{
  "error": "AISSTREAM_API_KEY not found in environment variables. Get a free API key at: https://aisstream.io"
}
```

Common errors:
- Missing or invalid API key
- Invalid coordinates (lat: -90 to 90, lon: -180 to 180)
- Invalid timeout (must be 3-60 seconds)
- Invalid MMSI (must be 9-digit number)
- Unknown port name

## Performance

- **WebSocket connection**: ~1-2 seconds to establish
- **Data collection**: Based on timeout parameter
- **Processing**: Instant (filtering and sorting)
- **Total response time**: ~timeout + 2 seconds

Example: `timeout=15` → total response ~17 seconds

## Security

- API key stored in `.env` (never in code)
- WebSocket connection uses WSS (secure)
- No persistent data storage
- All processing in-memory

## Dependencies

- `websocket-client`: WebSocket communication
- Python standard library: `json`, `time`, `math`, `threading`

## Troubleshooting

**No ships found:**
- Increase `timeout` (try 30-60 seconds)
- Increase `radius_km` (try 100-200 km)
- Check if area has AIS coverage (coastal areas work best)
- Verify API key is valid

**Connection timeout:**
- Check internet connection
- Verify AISStream.io is online
- Check firewall/proxy settings

**Invalid API key error:**
- Verify `AISSTREAM_API_KEY` in `.env`
- Get new key at https://aisstream.io
- Restart server after updating `.env`

## References

- AISStream.io API: https://aisstream.io/documentation
- AIS System: https://en.wikipedia.org/wiki/Automatic_identification_system
- MMSI Numbers: https://en.wikipedia.org/wiki/Maritime_Mobile_Service_Identity
