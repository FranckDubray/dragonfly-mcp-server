"""SQLite database operations for Vélib' cache (chroot to project)."""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from pathlib import Path
import sqlite3


def get_db_path() -> Path:
    """Get chrooted database path.
    
    Returns:
        Path to velib.db within project sqlite3/ directory
    """
    # Project root = 4 levels up from this file
    project_root = Path(__file__).parent.parent.parent.parent
    sqlite_dir = project_root / "sqlite3"
    
    # Ensure directory exists
    sqlite_dir.mkdir(parents=True, exist_ok=True)
    
    return sqlite_dir / "velib.db"


def init_database() -> Dict[str, Any]:
    """Initialize database schema.
    
    Returns:
        Dict with 'success' (bool) and optional 'error'
    """
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create stations table (only real API fields)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stations (
                station_code TEXT PRIMARY KEY,
                station_id INTEGER,
                name TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                capacity INTEGER,
                station_opening_hours TEXT
            )
        """)
        
        # Create metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stations_coords 
            ON stations(lat, lon)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stations_name 
            ON stations(name)
        """)
        
        conn.commit()
        conn.close()
        
        return {"success": True}
        
    except Exception as e:
        return {"success": False, "error": f"Failed to initialize database: {str(e)}"}


def clear_stations_table() -> Dict[str, Any]:
    """Clear all data from stations table.
    
    Returns:
        Dict with 'success' (bool) and optional 'error'
    """
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM stations")
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return {"success": True, "deleted_count": deleted_count}
        
    except Exception as e:
        return {"success": False, "error": f"Failed to clear stations: {str(e)}"}


def insert_stations(stations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Insert multiple stations (batch insert).
    
    Args:
        stations: List of station dicts
        
    Returns:
        Dict with 'success' (bool), 'inserted_count', and optional 'error'
    """
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        inserted_count = 0
        errors = []
        
        for station in stations:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO stations 
                    (station_code, station_id, name, lat, lon, capacity, station_opening_hours)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    station.get("station_code", ""),
                    station.get("station_id"),
                    station.get("name", ""),
                    station.get("lat", 0.0),
                    station.get("lon", 0.0),
                    station.get("capacity", 0),
                    station.get("station_opening_hours")
                ))
                inserted_count += 1
                
            except Exception as e:
                errors.append({
                    "station_code": station.get("station_code", "unknown"),
                    "error": str(e)
                })
        
        conn.commit()
        conn.close()
        
        result = {
            "success": True,
            "inserted_count": inserted_count,
            "total_stations": len(stations)
        }
        
        if errors:
            result["errors"] = errors[:10]  # Limit error list
            result["error_count"] = len(errors)
        
        return result
        
    except Exception as e:
        return {"success": False, "error": f"Failed to insert stations: {str(e)}"}


def update_metadata(key: str, value: str, updated_at: str) -> Dict[str, Any]:
    """Update metadata key-value pair.
    
    Args:
        key: Metadata key
        value: Metadata value
        updated_at: ISO timestamp
        
    Returns:
        Dict with 'success' (bool) and optional 'error'
    """
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO metadata (key, value, updated_at)
            VALUES (?, ?, ?)
        """, (key, value, updated_at))
        
        conn.commit()
        conn.close()
        
        return {"success": True}
        
    except Exception as e:
        return {"success": False, "error": f"Failed to update metadata: {str(e)}"}


def get_metadata(key: str) -> Optional[Dict[str, str]]:
    """Get metadata value by key.
    
    Args:
        key: Metadata key
        
    Returns:
        Dict with 'value' and 'updated_at' or None if not found
    """
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT value, updated_at FROM metadata WHERE key = ?
        """, (key,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {"value": row[0], "updated_at": row[1]}
        return None
        
    except Exception:
        return None


def get_station_count() -> int:
    """Get total number of stations in database.
    
    Returns:
        Station count
    """
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM stations")
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
        
    except Exception:
        return 0
