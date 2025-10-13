"""SMTP provider configurations and client initialization."""

import os
from typing import Dict, Any


class SMTPConfig:
    """SMTP provider configurations."""
    
    # Provider configurations (serveurs SMTP en dur)
    PROVIDERS = {
        "gmail": {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "use_tls": True,
            "env_email": "IMAP_GMAIL_EMAIL",      # Réutilise les vars IMAP
            "env_password": "IMAP_GMAIL_PASSWORD"  # Même credentials que IMAP
        },
        "infomaniak": {
            "smtp_host": "mail.infomaniak.com",
            "smtp_port": 587,
            "use_tls": True,
            "env_email": "IMAP_INFOMANIAK_EMAIL",
            "env_password": "IMAP_INFOMANIAK_PASSWORD"
        }
    }
    
    def __init__(self, provider: str = "gmail"):
        """Initialize SMTP config with credentials from environment.
        
        Args:
            provider: Email provider (gmail or infomaniak)
            
        Raises:
            ValueError: If provider invalid or credentials missing
        """
        self.provider = provider.lower()
        
        if self.provider not in self.PROVIDERS:
            raise ValueError(
                f"Invalid provider '{self.provider}'. "
                f"Must be one of: {', '.join(self.PROVIDERS.keys())}"
            )
        
        config = self.PROVIDERS[self.provider]
        
        # Get credentials from environment (IMAP variables)
        self.email = os.getenv(config["env_email"], "").strip()
        self.password = os.getenv(config["env_password"], "").strip()
        
        if not self.email:
            raise ValueError(
                f"{config['env_email']} not found in environment variables. "
                f"Configure {self.provider} credentials in .env"
            )
        
        if not self.password:
            raise ValueError(
                f"{config['env_password']} not found in environment variables. "
                f"For Gmail: use App Password. For Infomaniak: use email password."
            )
        
        # SMTP settings (en dur depuis config)
        self.host = config["smtp_host"]
        self.port = config["smtp_port"]
        self.use_tls = config["use_tls"]
