import smtplib
from email.message import EmailMessage
from typing import Optional

from flask import current_app


def send_email(
    to_email: str,
    subject: str,
    body: str,
    html: Optional[str] = None,
) -> Optional[str]:
    """Send an email using SMTP.

    - Always sends a plain-text body (for compatibility).
    - If `html` is provided, also attaches an HTML alternative.

    Returns:
        None on success, otherwise an error string.
    """
    cfg = current_app.config
    host = cfg.get("SMTP_HOST")
    port = int(cfg.get("SMTP_PORT", 587))
    user = cfg.get("SMTP_USER")
    pw = cfg.get("SMTP_PASS")
    from_email = cfg.get("SMTP_FROM") or user
    use_tls = bool(cfg.get("SMTP_USE_TLS", True))

    if not host or not from_email:
        return "SMTP is not configured (SMTP_HOST/SMTP_FROM)."

    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    # Plain text fallback
    msg.set_content(body)

    # Optional HTML alternative
    if html:
        msg.add_alternative(html, subtype="html")

    try:
        with smtplib.SMTP(host, port, timeout=10) as server:
            server.ehlo()
            if use_tls:
                server.starttls()
                server.ehlo()
            if user and pw:
                server.login(user, pw)
            server.send_message(msg)
        return None
    except Exception as e:
        return f"Failed to send email: {e}"
