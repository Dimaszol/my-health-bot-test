# webapp/email_service.py
# 📨 Отправка писем через Resend

import os
import logging
import resend

logger = logging.getLogger(__name__)


async def send_email(to_email: str, subject: str, html: str) -> bool:
    """Отправить письмо через Resend. Возвращает True если успешно."""

    api_key = os.getenv("RESEND_API_KEY", "")
    if not api_key:
        logger.error("RESEND_API_KEY не задан")
        return False

    email_from = os.getenv("EMAIL_FROM", "noreply@pulsebook.health")

    resend.api_key = api_key

    try:
        resend.Emails.send({
            "from": f"PulseBook <{email_from}>",
            "to": [to_email],
            "subject": subject,
            "html": html,
        })
        logger.info("Email sent | type=outbound")
        return True

    except Exception as e:
        logger.error(f"Email send error: {type(e).__name__}: {e}")
        return False