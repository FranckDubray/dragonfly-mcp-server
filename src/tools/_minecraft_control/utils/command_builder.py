"""
Minecraft command builder
"""
import logging
from ..config import TIME_VALUES

logger = logging.getLogger(__name__)

class CommandBuilder:
    """Build Minecraft commands"""
    
    @staticmethod
    def summon(entity_type: str, x: float, y: float, z: float, nbt: str = "") -> str:
        """Build /summon command"""
        pos = f"{x:.2f} {y:.2f} {z:.2f}"
        if nbt:
            return f"summon {entity_type} {pos} {nbt}"
        return f"summon {entity_type} {pos}"
    
    @staticmethod
    def fill(x1: float, y1: float, z1: float, 
             x2: float, y2: float, z2: float, block: str) -> str:
        """Build /fill command"""
        return f"fill {int(x1)} {int(y1)} {int(z1)} {int(x2)} {int(y2)} {int(z2)} {block}"
    
    @staticmethod
    def setblock(x: float, y: float, z: float, block: str) -> str:
        """Build /setblock command"""
        return f"setblock {int(x)} {int(y)} {int(z)} {block}"
    
    @staticmethod
    def tp(player: str, x: float, y: float, z: float, 
           yaw: float = None, pitch: float = None) -> str:
        """Build /tp command"""
        pos = f"{x:.2f} {y:.2f} {z:.2f}"
        if yaw is not None and pitch is not None:
            return f"tp {player} {pos} {yaw:.2f} {pitch:.2f}"
        return f"tp {player} {pos}"
    
    @staticmethod
    def weather(condition: str) -> str:
        """Build /weather command"""
        return f"weather {condition}"
    
    @staticmethod
    def time_set(preset: str = None, value: int = None) -> str:
        """Build /time set command"""
        if value is not None:
            return f"time set {value}"
        if preset and preset in TIME_VALUES:
            return f"time set {TIME_VALUES[preset]}"
        return f"time set {preset}"
    
    @staticmethod
    def gamemode(mode: str, player: str = "@p") -> str:
        """Build /gamemode command"""
        return f"gamemode {mode} {player}"
    
    @staticmethod
    def difficulty(level: str) -> str:
        """Build /difficulty command"""
        return f"difficulty {level}"
    
    @staticmethod
    def data_get(selector: str, path: str = None) -> str:
        """Build /data get command"""
        cmd = f"data get entity {selector}"
        if path:
            cmd += f" {path}"
        return cmd
