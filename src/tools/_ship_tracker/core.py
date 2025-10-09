"""Core logic for ship tracking operations."""

from typing import Dict, Any, List
from .services.aisstream import AISStreamClient, get_port_coordinates
from .validators import (
    validate_track_ships_params,
    validate_ship_details_params,
    validate_port_traffic_params
)
from .utils import (
    get_ship_type_name,
    get_navigation_status_name,
    knots_to_kmh,
    meters_to_feet,
    format_coordinates
)


def handle_track_ships(**params) -> Dict[str, Any]:
    """Handle track_ships operation.
    
    Args:
        **params: Track ships parameters
            - latitude (float, required): Center latitude (-90 to 90)
            - longitude (float, required): Center longitude (-180 to 180)
            - radius_km (float, optional): Search radius in km (1-500, default: 50)
            - ship_type (str, optional): Filter by ship type
            - min_length (float, optional): Minimum ship length in meters
            - max_length (float, optional): Maximum ship length in meters
            - min_speed_knots (float, optional): Minimum speed in knots
            - max_speed_knots (float, optional): Maximum speed in knots
            - navigation_status (str, optional): Filter by navigation status
            - max_results (int, optional): Maximum results (1-200, default: 50)
            - sort_by (str, optional): Sort by distance/speed/length (default: distance)
    
    Returns:
        Ships in the specified area with details
    """
    try:
        validated = validate_track_ships_params(params)
        client = AISStreamClient()
        
        # Get ships in area
        ships = client.get_ships_in_area(
            latitude=validated["latitude"],
            longitude=validated["longitude"],
            radius_km=validated["radius_km"],
            max_results=validated["max_results"]
        )
        
        # Apply filters
        filtered_ships = []
        for ship in ships:
            # Filter by ship type
            if validated["ship_type"]:
                ship_type_name = get_ship_type_name(ship.get("ship_type", 0)).lower()
                if validated["ship_type"] not in ship_type_name:
                    continue
            
            # Filter by length
            length = ship.get("length", 0)
            if validated["min_length"] and length < validated["min_length"]:
                continue
            if validated["max_length"] and length > validated["max_length"]:
                continue
            
            # Filter by speed
            speed = ship.get("speed", 0)
            if validated["min_speed_knots"] and speed < validated["min_speed_knots"]:
                continue
            if validated["max_speed_knots"] and speed > validated["max_speed_knots"]:
                continue
            
            # Filter by navigation status
            if validated["navigation_status"]:
                status_name = get_navigation_status_name(ship.get("navigation_status", 15)).lower()
                if validated["navigation_status"] not in status_name:
                    continue
            
            # Enrich ship data
            enriched_ship = {
                "mmsi": ship["mmsi"],
                "name": ship.get("name", "Unknown"),
                "ship_type": get_ship_type_name(ship.get("ship_type", 0)),
                "ship_type_code": ship.get("ship_type", 0),
                "position": {
                    "latitude": ship["latitude"],
                    "longitude": ship["longitude"],
                    "formatted": format_coordinates(ship["latitude"], ship["longitude"])
                },
                "distance_km": ship.get("distance_km", 0),
                "speed": {
                    "knots": round(ship.get("speed", 0), 1),
                    "kmh": round(knots_to_kmh(ship.get("speed", 0)), 1)
                },
                "heading": ship.get("heading"),
                "course": ship.get("course"),
                "navigation_status": get_navigation_status_name(ship.get("navigation_status", 15)),
                "destination": ship.get("destination", "Unknown"),
                "eta": ship.get("eta"),
                "dimensions": {
                    "length_m": ship.get("length"),
                    "length_ft": round(meters_to_feet(ship.get("length", 0)), 1) if ship.get("length") else None,
                    "width_m": ship.get("width"),
                    "draught_m": ship.get("draught")
                },
                "timestamp": ship.get("timestamp")
            }
            
            filtered_ships.append(enriched_ship)
        
        # Sort results
        sort_key = {
            "distance": lambda s: s["distance_km"],
            "speed": lambda s: s["speed"]["knots"],
            "length": lambda s: s["dimensions"]["length_m"] or 0
        }.get(validated["sort_by"], lambda s: s["distance_km"])
        
        filtered_ships.sort(key=sort_key, reverse=(validated["sort_by"] != "distance"))
        
        return {
            "success": True,
            "search_center": {
                "latitude": validated["latitude"],
                "longitude": validated["longitude"],
                "formatted": format_coordinates(validated["latitude"], validated["longitude"])
            },
            "radius_km": validated["radius_km"],
            "ships_found": len(filtered_ships),
            "ships": filtered_ships[:validated["max_results"]],
            "filters_applied": {
                "ship_type": validated["ship_type"],
                "min_length_m": validated["min_length"],
                "max_length_m": validated["max_length"],
                "min_speed_knots": validated["min_speed_knots"],
                "max_speed_knots": validated["max_speed_knots"],
                "navigation_status": validated["navigation_status"]
            }
        }
        
    except ValueError as e:
        return {"error": f"Validation error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def handle_get_ship_details(**params) -> Dict[str, Any]:
    """Handle get_ship_details operation.
    
    Args:
        **params: Ship details parameters
            - mmsi (int, required): Maritime Mobile Service Identity (9 digits)
    
    Returns:
        Detailed information about the ship
    """
    try:
        validated = validate_ship_details_params(params)
        client = AISStreamClient()
        
        ship = client.get_ship_by_mmsi(validated["mmsi"])
        
        if not ship:
            return {
                "error": f"Ship with MMSI {validated['mmsi']} not found"
            }
        
        return {
            "success": True,
            "mmsi": ship["mmsi"],
            "name": ship.get("name", "Unknown"),
            "imo": ship.get("imo"),
            "callsign": ship.get("callsign"),
            "ship_type": get_ship_type_name(ship.get("ship_type", 0)),
            "ship_type_code": ship.get("ship_type", 0),
            "country": ship.get("country"),
            "position": {
                "latitude": ship["latitude"],
                "longitude": ship["longitude"],
                "formatted": format_coordinates(ship["latitude"], ship["longitude"])
            },
            "speed": {
                "knots": round(ship.get("speed", 0), 1),
                "kmh": round(knots_to_kmh(ship.get("speed", 0)), 1)
            },
            "heading": ship.get("heading"),
            "course": ship.get("course"),
            "navigation_status": get_navigation_status_name(ship.get("navigation_status", 15)),
            "destination": ship.get("destination", "Unknown"),
            "eta": ship.get("eta"),
            "dimensions": {
                "length_m": ship.get("length"),
                "length_ft": round(meters_to_feet(ship.get("length", 0)), 1) if ship.get("length") else None,
                "width_m": ship.get("width"),
                "draught_m": ship.get("draught")
            },
            "timestamp": ship.get("timestamp"),
            "last_position_update": ship.get("last_position_update")
        }
        
    except ValueError as e:
        return {"error": f"Validation error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def handle_get_port_traffic(**params) -> Dict[str, Any]:
    """Handle get_port_traffic operation.
    
    Args:
        **params: Port traffic parameters
            - port_name (str, optional): Major port name (e.g., "Rotterdam", "Singapore")
            - latitude (float, optional): Port latitude (if port_name not provided)
            - longitude (float, optional): Port longitude (if port_name not provided)
            - radius_km (float, optional): Search radius in km (1-100, default: 10)
            - max_results (int, optional): Maximum results (default: 50)
    
    Returns:
        Ships near the specified port
    """
    try:
        validated = validate_port_traffic_params(params)
        
        # Resolve port coordinates
        if "port_name" in validated:
            port_data = get_port_coordinates(validated["port_name"])
            if not port_data:
                return {
                    "error": f"Port '{validated['port_name']}' not found in database. "
                            f"Please provide latitude and longitude instead."
                }
            validated["latitude"] = port_data["lat"]
            validated["longitude"] = port_data["lon"]
            port_info = {
                "name": validated["port_name"],
                "country": port_data.get("country")
            }
        else:
            port_info = {
                "coordinates": format_coordinates(validated["latitude"], validated["longitude"])
            }
        
        # Use track_ships logic with port-specific parameters
        track_params = {
            "latitude": validated["latitude"],
            "longitude": validated["longitude"],
            "radius_km": validated.get("radius_km", 10),
            "max_results": validated.get("max_results", 50)
        }
        
        result = handle_track_ships(**track_params)
        
        if result.get("success"):
            result["port"] = port_info
            result["traffic_summary"] = {
                "total_ships": result["ships_found"],
                "anchored": len([s for s in result["ships"] if "anchor" in s.get("navigation_status", "").lower()]),
                "underway": len([s for s in result["ships"] if "underway" in s.get("navigation_status", "").lower()]),
                "moored": len([s for s in result["ships"] if "moor" in s.get("navigation_status", "").lower()])
            }
        
        return result
        
    except ValueError as e:
        return {"error": f"Validation error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
