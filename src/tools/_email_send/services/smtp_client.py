"""SMTP client for sending emails via Gmail or Infomaniak."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import formataddr
from pathlib import Path
from typing import Dict, Any, List, Optional

from .smtp_config import SMTPConfig


class SMTPClient:
    """Client for sending emails via SMTP (Gmail or Infomaniak)."""
    
    def __init__(self, provider: str = "gmail"):
        """Initialize SMTP client.
        
        Args:
            provider: Email provider (gmail or infomaniak)
        """
        self.config = SMTPConfig(provider)
        self.provider = self.config.provider
        self.email = self.config.email
        self.password = self.config.password
        self.host = self.config.host
        self.port = self.config.port
        self.use_tls = self.config.use_tls
    
    def test_connection(self) -> Dict[str, Any]:
        """Test SMTP connection and authentication."""
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
            return {"success": False, "error": "Authentication failed. Check credentials."}
        except smtplib.SMTPException as e:
            return {"success": False, "error": f"SMTP error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Connection error: {str(e)}"}
    
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
            to: Recipient email addresses
            subject: Email subject
            body: Email body content
            body_type: Body type (text or html)
            cc: CC recipients
            bcc: BCC recipients
            reply_to: Reply-To address
            attachments: File paths to attach
            from_name: Sender display name
            priority: Email priority (low, normal, high)
        """
        try:
            msg = MIMEMultipart()
            
            # Set sender
            msg["From"] = formataddr((from_name, self.email)) if from_name else self.email
            msg["To"] = ", ".join(to)
            if cc:
                msg["Cc"] = ", ".join(cc)
            msg["Subject"] = subject
            if reply_to:
                msg["Reply-To"] = reply_to
            
            # Set priority
            priority_map = {"low": "5", "normal": "3", "high": "1"}
            msg["X-Priority"] = priority_map.get(priority, "3")
            
            # Attach body
            msg.attach(MIMEText(body, "html" if body_type == "html" else "plain", "utf-8"))
            
            # Attach files
            total_size = 0
            if attachments:
                for file_path in attachments:
                    path = Path(file_path)
                    if not path.exists():
                        return {"success": False, "error": f"Attachment not found: {file_path}"}
                    
                    file_size = path.stat().st_size
                    total_size += file_size
                    
                    if total_size > 25 * 1024 * 1024:
                        return {"success": False, "error": "Attachments exceed 25MB"}
                    
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
            return {"success": False, "error": "Authentication failed. Check credentials."}
        except smtplib.SMTPRecipientsRefused as e:
            return {"success": False, "error": f"Recipients refused: {str(e)}"}
        except smtplib.SMTPException as e:
            return {"success": False, "error": f"SMTP error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Send error: {str(e)}"}
