import asyncio
import logging
import smtplib
from email.message import EmailMessage
from typing import Optional

from app.core.config.settings import settings
from app.core.providers.email.base import EmailProvider, EmailAttachment, SendResult

logger = logging.getLogger(__name__)


class SMTPEmailProvider(EmailProvider):
    @property
    def provider_name(self) -> str:
        return "smtp"

    async def send(
        self,
        to: str,
        subject: str,
        html: str,
        attachments: Optional[list[EmailAttachment]] = None,
    ) -> SendResult:
        def _send_sync() -> SendResult:
            msg = EmailMessage()
            msg["From"] = settings.EMAIL_FROM
            msg["To"] = to
            msg["Subject"] = subject
            msg.set_content("Please view this email in an HTML-capable client.")
            msg.add_alternative(html, subtype="html")

            inline_attachments = [a for a in (attachments or []) if a.inline and a.content_id]
            if inline_attachments:
                html_part = msg.get_payload()[1]
                for att in inline_attachments:
                    html_part.add_related(
                        att.content,
                        maintype=att.mime_type.split("/")[0],
                        subtype=att.mime_type.split("/", 1)[1],
                        filename=att.filename,
                        cid=f"<{att.content_id}>",
                    )

            for att in attachments or []:
                maintype = att.mime_type.split("/")[0]
                subtype = att.mime_type.split("/", 1)[1]
                if att.inline and att.content_id:
                    continue  # already embedded inline above
                msg.add_attachment(
                        att.content,
                        maintype=maintype,
                        subtype=subtype,
                        filename=att.filename,
                    )

            try:
                if settings.SMTP_TLS:
                    server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30)
                    server.ehlo()
                    server.starttls()
                else:
                    server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30)
                try:
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)
                finally:
                    server.quit()
                return SendResult(status="sent")
            except Exception as e:
                logger.warning("SMTP send failed: %s", e)
                return SendResult(status="failed", error=str(e))

        return await asyncio.to_thread(_send_sync)
