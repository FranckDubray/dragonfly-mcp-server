"""
Minecraft Control configuration (hardcoded for localhost)
"""

# RCON Connection
RCON_HOST = "localhost"
RCON_PORT = 25575
RCON_PASSWORD = "toto"  # RCON password (change if different)
RCON_TIMEOUT = 30  # seconds (increased for slow responses)

# Limits
MAX_ENTITIES_PER_SPAWN = 1000
MAX_BLOCKS_PER_CHUNK = 32000  # Minecraft /fill limit
MAX_BATCH_COMMANDS = 100
BATCH_DELAY_MS = 50

# Timeouts & Retry
CONNECTION_RETRY_COUNT = 3
CONNECTION_RETRY_DELAY = 1  # seconds
COMMAND_TIMEOUT = 30  # seconds

# Paths
MODELS_DIR = "docs/models/"
ALLOWED_MODEL_EXTENSIONS = [".fbx", ".obj", ".stl", ".glb", ".gltf"]

# Voxelization
DEFAULT_VOXEL_RESOLUTION = 1.0
MIN_VOXEL_RESOLUTION = 0.1
MAX_VOXEL_RESOLUTION = 2.0
DEFAULT_MODEL_SCALE = 1.0

# Performance
THROTTLE_ENABLED = True
LARGE_OPERATION_THRESHOLD = 10000
CHUNK_PROCESSING_DELAY = 50  # ms

# Patterns
ENTITY_SPREAD_SPACING = 2.0
RANDOM_SPREAD_RADIUS = 10.0

# Geometry
SPHERE_PRECISION = 32
CYLINDER_PRECISION = 24

# Block Mapping
COLOR_MATCH_CACHE_SIZE = 1000
DEFAULT_FALLBACK_BLOCK = "stone"

# Logging
LOG_LEVEL = "INFO"
LOG_COMMANDS = True

# Minecraft Limits
WORLD_Y_MIN = -64
WORLD_Y_MAX = 320
WORLD_XZ_LIMIT = 30000000

# Time values
TIME_VALUES = {
    "day": 1000,
    "noon": 6000,
    "sunset": 12000,
    "night": 13000,
    "midnight": 18000,
    "sunrise": 23000
}

# Validation limits
VALIDATION_LIMITS = {
    "entity_count": {"min": 1, "max": 1000},
    "scale": {"min": 0.1, "max": 10.0},
    "voxel_resolution": {"min": 0.1, "max": 2.0},
    "dimensions": {
        "width": {"min": 1, "max": 500},
        "height": {"min": 1, "max": 320},
        "depth": {"min": 1, "max": 500}
    },
    "yaw": {"min": -180, "max": 180},
    "pitch": {"min": -90, "max": 90},
    "time_value": {"min": 0, "max": 24000},
    "delay_ms": {"min": 0, "max": 5000},
    "speed": {"min": 0.1, "max": 10.0}
}
