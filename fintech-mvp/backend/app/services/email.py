"""
Outbound email. If SMTP_HOST/SMTP_USER/SMTP_PASS are set, sends for real.
Otherwise (the default right now — no email provider is configured), it
logs the message instead, so the reset flow is fully testable and visible
in the server logs without needing real email set up yet.
"""
import logging
import os
import smtplib
from email.mime.text import MIMEText

logger = logging.getLogger("app.email")


def _configured() -> bool:
    return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_USER") and os.getenv("SMTP_PASS"))


def send_reset_email(to_email: str, reset_link: str) -> bool:
    """Returns True if actually emailed, False if only logged (dev fallback)."""
    subject = "Reset your password"
    body = (
        f"Someone requested a password reset for this account.\n\n"
        f"Reset your password: {reset_link}\n\n"
        f"This link expires in 30 minutes. If you didn't request this, ignore this email."
    )

    if not _configured():
        logger.warning("EMAIL NOT CONFIGURED — password reset link for %s: %s", to_email, reset_link)
        return False

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = os.getenv("FROM_EMAIL", os.getenv("SMTP_USER"))
    msg["To"] = to_email

    host, port = os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT", "587"))
    try:
        with smtplib.SMTP(host, port, timeout=10) as server:
            server.starttls()
            server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
            server.send_message(msg)
        return True
    except Exception:
        logger.exception("Failed to send reset email to %s — falling back to log", to_email)
        logger.warning("EMAIL SEND FAILED — password reset link for %s: %s", to_email, reset_link)
        return False
