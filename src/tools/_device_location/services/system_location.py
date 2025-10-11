"""
System-level location services (GPS/WiFi via native APIs).
Supports macOS (CoreLocation), Windows (Location API), Linux (GeoClue2).
"""
import platform
import subprocess
import logging
import json
import tempfile
import os

LOG = logging.getLogger(__name__)


def get_macos_location():
    """
    Get location on macOS using CoreLocation (GPS if available, else WiFi).
    Uses AppleScript for simplicity (no external dependencies).
    """
    # AppleScript that uses CoreLocation framework
    applescript = '''
    use framework "CoreLocation"
    use scripting additions

    set manager to current application's CLLocationManager's alloc()'s init()
    manager's requestWhenInUseAuthorization()
    
    set location to manager's location()
    if location is missing value then
        error "Location services unavailable or permission denied"
    end if
    
    set lat to location's coordinate()'s latitude as real
    set lon to location's coordinate()'s longitude as real
    set alt to location's altitude() as real
    set accuracy to location's horizontalAccuracy() as real
    set timestamp to location's timestamp() as «class isot»
    
    return "lat:" & lat & ",lon:" & lon & ",alt:" & alt & ",acc:" & accuracy
    '''
    
    try:
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            raise Exception(f"CoreLocation failed: {result.stderr.strip()}")
        
        # Parse result: "lat:48.8566,lon:2.3522,alt:35.0,acc:65.0"
        output = result.stdout.strip()
        parts = dict(item.split(':') for item in output.split(','))
        
        return {
            'source': 'macOS CoreLocation (GPS/WiFi)',
            'latitude': float(parts['lat']),
            'longitude': float(parts['lon']),
            'altitude': float(parts['alt']),
            'accuracy': float(parts['acc']),
        }
    except Exception as e:
        LOG.error(f"macOS CoreLocation failed: {e}")
        raise


def get_windows_location():
    """
    Get location on Windows using Windows Location API.
    Uses PowerShell to access Windows.Devices.Geolocation.
    """
    powershell_script = '''
    Add-Type -AssemblyName System.Device
    $watcher = New-Object System.Device.Location.GeoCoordinateWatcher
    $watcher.Start()
    Start-Sleep -Seconds 3
    
    if ($watcher.Position.Location.IsUnknown) {
        Write-Error "Location unavailable"
        exit 1
    }
    
    $loc = $watcher.Position.Location
    $json = @{
        latitude = $loc.Latitude
        longitude = $loc.Longitude
        altitude = $loc.Altitude
        accuracy = $loc.HorizontalAccuracy
    } | ConvertTo-Json
    
    Write-Output $json
    $watcher.Stop()
    '''
    
    try:
        result = subprocess.run(
            ['powershell', '-Command', powershell_script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            raise Exception(f"Windows Location API failed: {result.stderr.strip()}")
        
        data = json.loads(result.stdout.strip())
        
        return {
            'source': 'Windows Location API (GPS/WiFi)',
            'latitude': data['latitude'],
            'longitude': data['longitude'],
            'altitude': data.get('altitude'),
            'accuracy': data.get('accuracy'),
        }
    except Exception as e:
        LOG.error(f"Windows Location API failed: {e}")
        raise


def get_linux_location():
    """
    Get location on Linux using GeoClue2 D-Bus service.
    Requires geoclue2 to be installed and running.
    """
    try:
        # Try using gdbus (part of GLib, usually pre-installed)
        script = '''
        gdbus call --system \
        --dest org.freedesktop.GeoClue2 \
        --object-path /org/freedesktop/GeoClue2/Manager \
        --method org.freedesktop.GeoClue2.Manager.GetClient
        '''
        
        # This is complex - GeoClue2 requires async setup
        # For now, raise NotImplementedError
        raise NotImplementedError("Linux GeoClue2 support requires additional implementation")
        
    except Exception as e:
        LOG.error(f"Linux GeoClue2 failed: {e}")
        raise


def get_system_location():
    """
    Get location using system APIs (GPS if available, else WiFi).
    Automatically detects OS and uses appropriate API.
    
    Returns:
        dict: Location data with source, coordinates, accuracy
    
    Raises:
        Exception: If system location is unavailable or permission denied
    """
    system = platform.system()
    
    if system == 'Darwin':  # macOS
        return get_macos_location()
    elif system == 'Windows':
        return get_windows_location()
    elif system == 'Linux':
        return get_linux_location()
    else:
        raise NotImplementedError(f"System location not supported on {system}")
