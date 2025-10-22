"""
RCON client using mcipc (session-per-command)
"""
import logging
import time
import re
from typing import Optional, List

logger = logging.getLogger(__name__)

# Import config with error handling
try:
    from ..config import (
        RCON_HOST, RCON_PORT, RCON_PASSWORD, RCON_TIMEOUT,
        CONNECTION_RETRY_COUNT, CONNECTION_RETRY_DELAY, BATCH_DELAY_MS
    )
except ImportError as e:
    logger.error(f"Failed to import config: {e}")
    RCON_HOST = "localhost"
    RCON_PORT = 25575
    RCON_PASSWORD = "toto"
    RCON_TIMEOUT = 30
    CONNECTION_RETRY_COUNT = 3
    CONNECTION_RETRY_DELAY = 1
    BATCH_DELAY_MS = 50

class RconError(Exception):
    """RCON operation error"""
    pass

class RconClient:
    """RCON client wrapper opening a short-lived session per command.
    
    Using mcipc.rcon.je.Client as a context manager ensures proper
    auth/login and response handling, avoiding stale sockets/timeouts.
    """
    
    def __init__(self, host: str = RCON_HOST, port: int = RCON_PORT, 
                 password: str = RCON_PASSWORD, timeout: int = RCON_TIMEOUT):
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout
    
    def execute(self, command: str) -> str:
        """Execute a single command (opens a fresh RCON session)."""
        try:
            from mcipc.rcon.je import Client
        except ImportError:
            raise RconError("mcipc not installed. Run: pip install mcipc>=2.4.0")
        
        cmd = command.lstrip('/')
        logger.debug(f"Executing: /{cmd}")
        start = time.time()
        try:
            with Client(self.host, self.port, passwd=self.password, timeout=self.timeout) as c:
                if cmd == 'list' and hasattr(c, 'list'):
                    response = c.list()
                else:
                    response = c.run(cmd)
            elapsed = time.time() - start
            logger.debug(f"Command executed in {elapsed:.2f}s")
            return "" if response is None else str(response)
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"Command execution error after {elapsed:.2f}s: {e}")
            raise RconError(f"Command failed: {e}")
    
    def execute_batch(self, commands: list[str], delay_ms: int = BATCH_DELAY_MS) -> list[dict]:
        results = []
        delay_s = delay_ms / 1000.0
        for i, cmd in enumerate(commands):
            try:
                response = self.execute(cmd)
                results.append({
                    "command": cmd,
                    "response": response,
                    "success": True,
                    "index": i
                })
            except Exception as e:
                results.append({
                    "command": cmd,
                    "response": str(e),
                    "success": False,
                    "index": i
                })
                logger.warning(f"Batch command {i} failed: {e}")
            if i < len(commands) - 1 and delay_ms > 0:
                time.sleep(delay_s)
        return results
    
    def get_online_players(self) -> List[str]:
        """Return list of online player names by parsing /list output."""
        try:
            raw = self.execute('list')
            players: List[str] = []
            # mcipc style: Players(online=0, max=20, players=[...])
            m = re.search(r"players=\[(.*)\]", raw)
            if m is not None:
                inside = m.group(1).strip()
                if inside:
                    players = [p.strip() for p in inside.split(',') if p.strip()]
                return players
            # Vanilla style: There are N of a max ...: name1, name2
            m2 = re.search(r"players online:\s*(.*)$", raw)
            if m2 is not None:
                names = m2.group(1).strip()
                if names:
                    players = [p.strip() for p in names.split(',') if p.strip()]
            return players
        except Exception as e:
            logger.warning(f"Failed to get online players: {e}")
            return []
    
    def get_player_data(self, player: str = "@p", path: Optional[str] = None) -> dict:
        """Get player NBT directly via data get (reliable with RCON).
        Resolves @p → single online player if possible.
        """
        target = player
        if player == '@p':
            online = self.get_online_players()
            if len(online) == 1:
                target = online[0]
        # Direct command (no execute/@s indirection)
        cmd = f"data get entity {target}"
        if path:
            cmd += f" {path}"
        try:
            response = self.execute(cmd)
            return self._parse_nbt_response(response)
        except Exception as e:
            logger.warning(f"Failed to get player data for {target}: {e}")
            return {}
    
    def _parse_nbt_response(self, response: str) -> dict:
        result = {}
        pos_match = re.search(r'Pos:\s*\[([-\d.]+)d?,\s*([-\d.]+)d?,\s*([-\d.]+)d?\]', response)
        if pos_match:
            result['Pos'] = {
                'x': float(pos_match.group(1)),
                'y': float(pos_match.group(2)),
                'z': float(pos_match.group(3))
            }
        rot_match = re.search(r'Rotation:\s*\[([-\d.]+)f?,\s*([-\d.]+)f?\]', response)
        if rot_match:
            result['Rotation'] = {
                'yaw': float(rot_match.group(1)),
                'pitch': float(rot_match.group(2))
            }
        return result
    
    def test_connection(self) -> bool:
        try:
            logger.info("Testing RCON connection with /list command")
            _ = self.execute("list")
            logger.info("Connection test successful")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
