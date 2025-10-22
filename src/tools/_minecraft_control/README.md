# Minecraft Control Tool

RCON-based Minecraft server control with 8 operations.

## Setup

### 1. Install dependencies

```bash
pip install mcipc>=2.4.0
pip install trimesh[easy]>=4.0.0  # For 3D model import
pip install numpy>=1.24.0
```

### 2. Configure Minecraft server

Edit `server.properties`:

```ini
enable-rcon=true
rcon.port=25575
rcon.password=
```

**Note**: Empty password for localhost (default config)

### 3. Start Minecraft server

```bash
java -Xmx2G -Xms1G -jar server.jar nogui
```

## Operations

### 1. execute_command

Execute raw Minecraft command.

```python
{
    "operation": "execute_command",
    "command": "say Hello World"
}
```

### 2. spawn_entities

Spawn entities with patterns.

```python
{
    "operation": "spawn_entities",
    "entity_type": "horse",
    "count": 20,
    "spread_pattern": "circle",
    "relative_to_player": true,
    "offset": {"forward": 10, "up": 0, "right": 0}
}
```

**Patterns**: `line`, `circle`, `grid`, `random`

### 3. build_structure

Build geometric structures.

```python
{
    "operation": "build_structure",
    "block_type": "gold_block",
    "shape": "pyramid",
    "dimensions": {"width": 50, "height": 25, "depth": 50},
    "relative_to_player": true,
    "offset": {"forward": 30}
}
```

**Shapes**: `cube`, `sphere`, `pyramid`, `cylinder`, `wall`, `platform`

### 4. import_3d_model

Import 3D models as voxels.

```python
{
    "operation": "import_3d_model",
    "model_path": "castle.fbx",
    "scale": 2.0,
    "voxel_resolution": 1.0,
    "material_mapping": "color",
    "relative_to_player": true,
    "offset": {"forward": 50}
}
```

**Formats**: FBX, OBJ, STL, GLB, GLTF  
**Place models in**: `docs/models/`

### 5. control_player

Control player actions.

```python
# Teleport
{
    "operation": "control_player",
    "player_action": "teleport",
    "target_position": {"x": 100, "y": 64, "z": 200}
}

# Look direction
{
    "operation": "control_player",
    "player_action": "look",
    "yaw": 90,
    "pitch": -30
}

# Change gamemode
{
    "operation": "control_player",
    "player_action": "gamemode",
    "gamemode": "creative"
}
```

### 6. set_environment

Change world environment.

```python
{
    "operation": "set_environment",
    "weather": "rain",
    "time": "midnight",
    "difficulty": "hard"
}
```

**Weather**: `clear`, `rain`, `thunder`  
**Time**: `day`, `night`, `noon`, `midnight`, `sunrise`, `sunset`  
**Difficulty**: `peaceful`, `easy`, `normal`, `hard`

### 7. batch_commands

Execute multiple commands.

```python
{
    "operation": "batch_commands",
    "commands": [
        "say Starting sequence",
        "weather clear",
        "time set day",
        "gamemode creative @a"
    ],
    "delay_ms": 100
}
```

### 8. get_player_state

Get player position and rotation.

```python
{
    "operation": "get_player_state",
    "player_name": "@p"
}
```

## Conversational Examples

### "Spawn 20 zebras approaching player"

```python
{
    "operation": "spawn_entities",
    "entity_type": "horse",
    "count": 20,
    "spread_pattern": "line",
    "nbt_data": {"CustomName": '{"text":"Zebra"}', "Variant": 2},
    "relative_to_player": true,
    "offset": {"forward": 15}
}
```

### "Build golden pyramid 50x50 in front of player"

```python
{
    "operation": "build_structure",
    "block_type": "gold_block",
    "shape": "pyramid",
    "dimensions": {"width": 50, "height": 25, "depth": 50},
    "relative_to_player": true,
    "offset": {"forward": 30}
}
```

### "Make it rain and night time"

```python
{
    "operation": "set_environment",
    "weather": "rain",
    "time": "midnight"
}
```

### "Player jumps high"

```python
{
    "operation": "execute_command",
    "command": "effect give @p jump_boost 30 5"
}
```

## Architecture

```
_minecraft_control/
├── api.py              # Router
├── core.py             # Orchestration
├── config.py           # Hard-coded config
├── client/
│   └── rcon_client.py  # mcipc wrapper
├── operations/
│   ├── command.py
│   ├── entities.py
│   ├── structures.py
│   ├── models.py
│   ├── player.py
│   ├── environment.py
│   ├── batch.py
│   └── state.py
├── geometry/
│   ├── shapes.py       # 3D shapes
│   ├── patterns.py     # Spread patterns
│   └── coordinates.py  # Position calc
├── voxel/
│   ├── voxelizer.py    # 3D → voxels
│   └── block_mapper.py # Voxels → blocks
└── utils/
    ├── validators.py
    ├── command_builder.py
    ├── chunker.py
    └── nbt_builder.py
```

## Limits

- **RCON**: Must be enabled on server
- **Max entities/spawn**: 1000
- **Max blocks/fill**: 32000 (auto-chunked)
- **3D models**: Limited to 100k voxels (safety)
- **Batch commands**: Max 100
- **Output truncation**: Results limited to 50 items (configurable with `limit` param)

## Troubleshooting

### "mcipc not installed"

```bash
pip install mcipc>=2.4.0
```

### "RCON connection failed"

Check `server.properties`:
- `enable-rcon=true`
- `rcon.port=25575`
- Server is running

### "trimesh not installed" (for 3D models)

```bash
pip install trimesh[easy]
```

### Large structures lag server

- Reduce dimensions
- Increase `delay_ms` in params
- Use `hollow=true` for structures

## Logging

Set `LOG_LEVEL` in `config.py`:
- `INFO`: Normal operations
- `DEBUG`: Detailed command logs
- `WARNING`: Errors only

Logs show:
- Command execution
- Voxelization progress
- Chunking info
- Error details
