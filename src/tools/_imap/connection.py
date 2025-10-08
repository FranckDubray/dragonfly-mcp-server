"""
IMAP connection management (SSL, login, logout)
"""
from __future__ import annotations
import imaplib
import ssl
from typing import Dict, Any, Optional
from .presets import get_preset, IMAP_PRESETS


class IMAPConnection:
    """Manages a single IMAP connection with proper cleanup"""
    
    def __init__(self, provider: str, email: str, password: str, 
                 imap_server: Optional[str] = None, 
                 imap_port: Optional[int] = None,
                 use_ssl: bool = True,
                 timeout: int = 30):
        self.provider = provider
        self.email = email
        self.password = password
        self.timeout = timeout
        self.connection: Optional[imaplib.IMAP4_SSL | imaplib.IMAP4] = None
        
        # Get preset config
        preset = get_preset(provider)
        
        # Override with custom params if provided
        self.server = imap_server or preset.get("server")
        self.port = imap_port or preset.get("port", 993 if use_ssl else 143)
        self.use_ssl = use_ssl if use_ssl is not None else preset.get("ssl", True)
        
        if not self.server:
            raise ValueError(f"IMAP server not specified. Provider '{provider}' requires imap_server parameter.")
    
    def connect(self) -> Dict[str, Any]:
        """Establish IMAP connection and login"""
        try:
            # Create connection
            if self.use_ssl:
                context = ssl.create_default_context()
                self.connection = imaplib.IMAP4_SSL(
                    self.server, 
                    self.port, 
                    ssl_context=context,
                    timeout=self.timeout
                )
            else:
                self.connection = imaplib.IMAP4(self.server, self.port, timeout=self.timeout)
            
            # Login
            self.connection.login(self.email, self.password)
            
            # Get capabilities and folder list
            capabilities = self.connection.capabilities
            status, folders_data = self.connection.list()
            folders_count = len(folders_data) if status == 'OK' else 0
            
            return {
                "success": True,
                "provider": self.provider,
                "server": self.server,
                "port": self.port,
                "ssl": self.use_ssl,
                "email": self.email,
                "capabilities": [c.decode() if isinstance(c, bytes) else c for c in capabilities],
                "folders_count": folders_count,
                "notes": IMAP_PRESETS.get(self.provider, {}).get("notes", "")
            }
        
        except imaplib.IMAP4.error as e:
            return {
                "success": False,
                "error": f"IMAP error: {str(e)}",
                "hint": "Check email/password. For Gmail/Yahoo/iCloud: use App Password if 2FA enabled."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Connection failed: {str(e)}",
                "server": self.server,
                "port": self.port
            }
    
    def disconnect(self):
        """Properly close IMAP connection"""
        if self.connection:
            try:
                self.connection.logout()
            except Exception:
                pass
            self.connection = None
    
    def __enter__(self):
        result = self.connect()
        if not result.get("success"):
            raise ConnectionError(result.get("error", "Connection failed"))
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
