import logging
from typing import Optional

from app.core.config.settings import settings, _is_placeholder
from app.core.providers.email.base import EmailProvider

logger = logging.getLogger(__name__)


def get_email_provider(provider: Optional[str] = None) -> Optional[EmailProvider]:
    provider_name = provider or settings.EMAIL_PROVIDER

    if provider_name == "smtp":
        if not settings.SMTP_HOST or _is_placeholder(settings.SMTP_PASSWORD):
            logger.warning("SMTP_HOST / SMTP_PASSWORD not configured - smtp provider unavailable")
            return None
        from app.core.providers.email.smtp import SMTPEmailProvider

        return SMTPEmailProvider()

    logger.warning("Unsupported email provider: %s", provider_name)
    return None