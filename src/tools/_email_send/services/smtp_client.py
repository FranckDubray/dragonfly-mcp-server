"""SMTP client for sending emails via Gmail or Infomaniak."""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import formataddr
from pathlib import Path
from typing import Dict, Any, List, Optional


class SMTPClient:
    """Client for sending emails via SMTP (Gmail or Infomaniak)."""
    
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
        """Initialize SMTP client with credentials from environment.
        
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
    
    def test_connection(self) -> Dict[str, Any]:
        """Test SMTP connection and authentication.
        
        Returns:
            Dict with success status and connection info
        """
        try:
            if self.use_tls:
                server = smtplib.SMTP(self.host, self.port, timeout=10)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=10)
            
            server.login(self.email, self.password)
            server.quit()
            
            return {
                "success": True,
                "provider": self.provider,
                "host": self.host,
                "port": self.port,
                "email": self.email,
                "message": "SMTP connection successful"
            }
            
        except smtplib.SMTPAuthenticationError:
            return {
                "success": False,
                "error": "Authentication failed. Check your email and password/app password."
            }
        except smtplib.SMTPException as e:
            return {
                "success": False,
                "error": f"SMTP error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Connection error: {str(e)}"
            }
    
    def send(
        self,
        to: List[str],
        subject: str,
        body: str,
        body_type: str = "text",
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[str]] = None,
        from_name: Optional[str] = None,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """Send email via SMTP.
        
        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body content
            body_type: Body type (text or html)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            reply_to: Reply-To address (optional)
            attachments: List of file paths to attach (optional)
            from_name: Sender display name (optional)
            priority: Email priority (low, normal, high)
            
        Returns:
            Dict with success status and message info
        """
        try:
            # Create message
            msg = MIMEMultipart()
            
            # Set sender
            if from_name:
                msg["From"] = formataddr((from_name, self.email))
            else:
                msg["From"] = self.email
            
            # Set recipients
            msg["To"] = ", ".join(to)
            if cc:
                msg["Cc"] = ", ".join(cc)
            
            msg["Subject"] = subject
            
            # Set reply-to
            if reply_to:
                msg["Reply-To"] = reply_to
            
            # Set priority
            priority_map = {"low": "5", "normal": "3", "high": "1"}
            msg["X-Priority"] = priority_map.get(priority, "3")
            
            # Attach body
            if body_type == "html":
                msg.attach(MIMEText(body, "html", "utf-8"))
            else:
                msg.attach(MIMEText(body, "plain", "utf-8"))
            
            # Attach files
            total_size = 0
            if attachments:
                for file_path in attachments:
                    path = Path(file_path)
                    if not path.exists():
                        return {
                            "success": False,
                            "error": f"Attachment not found: {file_path}"
                        }
                    
                    file_size = path.stat().st_size
                    total_size += file_size
                    
                    # Check total size (25MB limit)
                    if total_size > 25 * 1024 * 1024:
                        return {
                            "success": False,
                            "error": "Total attachments size exceeds 25MB"
                        }
                    
                    with open(path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=path.name)
                        part["Content-Disposition"] = f'attachment; filename="{path.name}"'
                        msg.attach(part)
            
            # Connect and send
            if self.use_tls:
                server = smtplib.SMTP(self.host, self.port, timeout=30)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=30)
            
            server.login(self.email, self.password)
            
            # Build recipient list (to + cc + bcc)
            all_recipients = to + (cc or []) + (bcc or [])
            
            server.sendmail(self.email, all_recipients, msg.as_string())
            server.quit()
            
            return {
                "success": True,
                "message": "Email sent successfully",
                "from": self.email,
                "to": to,
                "cc": cc or [],
                "bcc_count": len(bcc) if bcc else 0,
                "subject": subject,
                "attachments_count": len(attachments) if attachments else 0,
                "attachments_size_bytes": total_size
            }
            
        except smtplib.SMTPAuthenticationError:
            return {
                "success": False,
                "error": "Authentication failed. Check your email and password/app password."
            }
        except smtplib.SMTPRecipientsRefused as e:
            return {
                "success": False,
                "error": f"Recipients refused: {str(e)}"
            }
        except smtplib.SMTPException as e:
            return {
                "success": False,
                "error": f"SMTP error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Send error: {str(e)}"
            }
