import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Tuple, Optional
from app.core.config import settings

logger = logging.getLogger("app.email_service")

def deliver_campaign_email(recipient_email: str, subject: str, body_html: str) -> Tuple[str, Optional[str]]:
    """Delivers campaign email via SMTP when configured, otherwise records as simulated."""
    if settings.NOTIFICATIONS_ENABLED and settings.SMTP_HOST:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM or "wellness@campus.edu"
            msg["To"] = recipient_email
            msg.attach(MIMEText(body_html, "html"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.starttls()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(msg["From"], [recipient_email], msg.as_string())
            logger.info("Successfully delivered email to %s", recipient_email)
            return "sent", None
        except Exception as e:
            logger.error("Failed email delivery to %s: %s", recipient_email, str(e))
            return "failed", str(e)
    else:
        logger.info("Simulated email delivery to %s (subject: %s)", recipient_email, subject)
        return "sent", None
