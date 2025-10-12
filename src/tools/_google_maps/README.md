# Google Maps Tool

Complete Google Maps API integration for Dragonfly MCP Server.

## Architecture

```
_google_maps/
├── __init__.py           # Package init
├── api.py                # Route operations (1.6 KB)
├── core.py               # Business logic (10.5 KB)
├── formatters.py         # Response formatters (6.2 KB) 
├── validators.py         # Input validation (2.9 KB)
└── services/
    ├── __init__.py       # Services init
    └── api_client.py     # Google Maps API client (2.4 KB)
```

**Total**: 7 files, ~23.6 KB

## Operations (9)

| Operation | Description | Required Params | Optional Params |
|-----------|-------------|-----------------|-----------------|
| `geocode` | Address → Coordinates | `address` | `language`, `limit` |
| `reverse_geocode` | Coordinates → Address | `lat`, `lon` | `language`, `limit` |
| `directions` | Route between 2 points | `origin`, `destination` | `mode`, `alternatives`, `avoid`, `departure_time`, `arrival_time`, `language` |
| `distance_matrix` | Distances between multiple points | `origins`, `destinations` | `mode`, `avoid`, `departure_time`, `language` |
| `places_search` | Search places by text | `query` | `language`, `limit` |
| `place_details` | Detailed place info | `place_id` | `language` |
| `places_nearby` | Search nearby places | `lat`, `lon` | `radius`, `type`, `keyword`, `language`, `limit` |
| `timezone` | Timezone for coordinates | `lat`, `lon` | - |
| `elevation` | Elevation for coordinates | `lat`, `lon` | - |

## Configuration

**Token fallback logic**:
1. `GOOGLE_MAPS_API_KEY` (specific, priority)
2. `GOOGLE_API_KEY` (generic fallback)

If neither is set, tool returns error.

**Free tier**: $200 credit/month (~28,500 geocoding requests or ~40,000 map loads)

## Examples

### Geocode address
```json
{
  "operation": "geocode",
  "address": "Eiffel Tower, Paris"
}
```

**Response**:
```json
{
  "query": "Eiffel Tower, Paris",
  "results": [
    {
      "formatted_address": "Champ de Mars, 5 Av. Anatole France, 75007 Paris, France",
      "place_id": "ChIJLU7jZClu5kcR4PcOOO6p3I0",
      "types": ["tourist_attraction", "point_of_interest", "establishment"],
      "coordinates": {
        "lat": 48.8583701,
        "lon": 2.2944813
      },
      "location_type": "ROOFTOP",
      "address_components": [...]
    }
  ],
  "total_count": 1,
  "returned_count": 1
}
```

### Reverse geocode
```json
{
  "operation": "reverse_geocode",
  "lat": 48.8584,
  "lon": 2.2945
}
```

**Response**:
```json
{
  "coordinates": {
    "lat": 48.8584,
    "lon": 2.2945
  },
  "results": [
    {
      "formatted_address": "5 Av. Anatole France, 75007 Paris, France",
      "place_id": "ChIJLU7jZClu5kcR4PcOOO6p3I0",
      "types": ["street_address"],
      "coordinates": {...}
    }
  ],
  "total_count": 5,
  "returned_count": 5
}
```

### Directions
```json
{
  "operation": "directions",
  "origin": "Paris, France",
  "destination": "Lyon, France",
  "mode": "driving"
}
```

**Response**:
```json
{
  "origin": "Paris, France",
  "destination": "Lyon, France",
  "mode": "driving",
  "routes": [
    {
      "summary": "A6",
      "legs": [
        {
          "start_address": "Paris, France",
          "end_address": "Lyon, France",
          "distance": {
            "meters": 463000,
            "text": "463 km"
          },
          "duration": {
            "seconds": 15480,
            "text": "4 hours 18 mins"
          },
          "steps": [...]
        }
      ],
      "overview_polyline": "..."
    }
  ],
  "routes_count": 1
}
```

### Distance matrix
```json
{
  "operation": "distance_matrix",
  "origins": ["Paris, France", "Lyon, France"],
  "destinations": ["Marseille, France", "Nice, France"],
  "mode": "driving"
}
```

**Response**:
```json
{
  "mode": "driving",
  "matrix": [
    {
      "origin": "Paris, France",
      "destination": "Marseille, France",
      "distance": { "meters": 775000, "text": "775 km" },
      "duration": { "seconds": 26100, "text": "7 hours 15 mins" }
    },
    {
      "origin": "Paris, France",
      "destination": "Nice, France",
      "distance": { "meters": 933000, "text": "933 km" },
      "duration": { "seconds": 31200, "text": "8 hours 40 mins" }
    },
    {
      "origin": "Lyon, France",
      "destination": "Marseille, France",
      "distance": { "meters": 315000, "text": "315 km" },
      "duration": { "seconds": 10800, "text": "3 hours" }
    },
    {
      "origin": "Lyon, France",
      "destination": "Nice, France",
      "distance": { "meters": 473000, "text": "473 km" },
      "duration": { "seconds": 15900, "text": "4 hours 25 mins" }
    }
  ],
  "total_combinations": 4
}
```

### Places search
```json
{
  "operation": "places_search",
  "query": "restaurants near Eiffel Tower",
  "limit": 10
}
```

**Response**:
```json
{
  "query": "restaurants near Eiffel Tower",
  "results": [
    {
      "name": "Madame Brasserie",
      "place_id": "ChIJ...",
      "formatted_address": "Champ de Mars, Paris",
      "coordinates": { "lat": 48.8584, "lon": 2.2945 },
      "types": ["restaurant", "food"],
      "rating": 4.2,
      "user_ratings_total": 1234,
      "price_level": 3,
      "opening_hours_open_now": true
    }
  ],
  "total_count": 20,
  "returned_count": 10,
  "truncated": true,
  "message": "Results truncated: 20 total, showing 10"
}
```

### Place details
```json
{
  "operation": "place_details",
  "place_id": "ChIJLU7jZClu5kcR4PcOOO6p3I0"
}
```

**Response**:
```json
{
  "place_id": "ChIJLU7jZClu5kcR4PcOOO6p3I0",
  "details": {
    "name": "Eiffel Tower",
    "formatted_address": "Champ de Mars, 5 Av. Anatole France, 75007 Paris, France",
    "coordinates": { "lat": 48.8583701, "lon": 2.2944813 },
    "types": ["tourist_attraction", "point_of_interest"],
    "rating": 4.7,
    "user_ratings_total": 387265,
    "formatted_phone_number": "+33 892 70 12 39",
    "website": "https://www.toureiffel.paris",
    "opening_hours": {
      "open_now": true,
      "weekday_text": [
        "Monday: 9:30 AM – 11:45 PM",
        "Tuesday: 9:30 AM – 11:45 PM",
        ...
      ]
    },
    "photos": [...]
  }
}
```

### Places nearby
```json
{
  "operation": "places_nearby",
  "lat": 48.8584,
  "lon": 2.2945,
  "radius": 500,
  "type": "restaurant"
}
```

**Response**:
```json
{
  "coordinates": { "lat": 48.8584, "lon": 2.2945 },
  "radius": 500,
  "type": "restaurant",
  "keyword": null,
  "results": [...],
  "total_count": 15,
  "returned_count": 15
}
```

### Timezone
```json
{
  "operation": "timezone",
  "lat": 48.8584,
  "lon": 2.2945
}
```

**Response**:
```json
{
  "coordinates": { "lat": 48.8584, "lon": 2.2945 },
  "timezone_id": "Europe/Paris",
  "timezone_name": "Central European Standard Time",
  "raw_offset": 3600,
  "dst_offset": 3600
}
```

### Elevation
```json
{
  "operation": "elevation",
  "lat": 48.8584,
  "lon": 2.2945
}
```

**Response**:
```json
{
  "coordinates": { "lat": 48.8584, "lon": 2.2945 },
  "elevation": 35.52,
  "resolution": 19.08
}
```

## Error Handling

All operations return structured errors:

```json
{
  "error": "Address 'XYZ' not found",
  "error_type": "ValueError"
}
```

**Common errors**:
- **Missing token**: `"Missing Google API token. Set either GOOGLE_MAPS_API_KEY or GOOGLE_API_KEY in .env"`
- **API denied**: `"API request denied: You must enable Billing..."`
- **Invalid params**: `"lat must be a number between -90 and 90"`
- **Not found**: `"Address 'XYZ' not found"` or `"No route found between origin and destination"`
- **Quota exceeded**: `"API quota exceeded"`

## Logging

All operations log with structured messages:
- **INFO**: Operation start (e.g., `"Geocoding address: Eiffel Tower"`)
- **WARNING**: Not found, truncation, API issues (e.g., `"Places search truncated: 50 → 20"`)
- **ERROR**: API errors (logged by `api_client.py`)

## Validation

**Strict validation** (see `validators.py`):
- **Coordinates**: `lat` ∈ [-90, 90], `lon` ∈ [-180, 180]
- **Arrays**: `origins`/`destinations` max 25 items each
- **Limits**: `limit` ∈ [1, 60], `radius` ∈ [1, 50000]
- **Required params**: Operation-specific (e.g., `geocode` requires `address`)

## Truncation

Operations returning lists support truncation warnings:
- **Default limit**: 20
- **Max limit**: 60
- **Warning**: `truncated: true` + `message` if `total_count > returned_count`

**Example**:
```json
{
  "results": [...],
  "total_count": 50,
  "returned_count": 20,
  "truncated": true,
  "message": "Results truncated: 50 total, showing 20"
}
```

## Performance

- **Timeout**: 15s per API request (configurable in `api_client.py`)
- **No caching**: All requests hit Google Maps API directly
- **Rate limits**: Free tier ~50 QPS, standard tier ~100 QPS

## Conformity Checklist

- [x] **Category**: `utilities` (JSON spec)
- [x] **Tags**: `maps`, `geocoding`, `directions`, `places`, `navigation`
- [x] **Validation**: Strict (coords, arrays, required params)
- [x] **Error handling**: Try-catch global, detailed errors
- [x] **Logging**: INFO/WARNING (all operations)
- [x] **Truncation warnings**: Yes (places_search, places_nearby, geocode, reverse_geocode)
- [x] **Counts**: `total_count` vs `returned_count`
- [x] **Outputs**: Minimal (no verbose `success`/`operation` fields)
- [x] **Timeouts**: 15s
- [x] **Defaults**: All explicit in JSON spec
- [x] **Token fallback**: `GOOGLE_MAPS_API_KEY` → `GOOGLE_API_KEY`
- [x] **README**: Complete (this file)
- [ ] **Files < 7KB**: `core.py` = 10.5 KB (⚠️ TODO: split)

## Known Issues

- **core.py > 7KB**: Needs further splitting (extract common patterns)
- **No caching**: Frequent identical requests may hit quota

## Future Improvements

1. Split `core.py` into operation-specific modules (geocoding.py, directions.py, places.py)
2. Add response caching (SQLite) for geocoding/reverse_geocode
3. Support pagination for places_search (next_page_token)
4. Add batch geocoding support
