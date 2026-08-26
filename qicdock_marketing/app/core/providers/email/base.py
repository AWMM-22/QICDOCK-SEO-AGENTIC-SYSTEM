from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EmailAttachment:
    filename: str
    content: bytes
    mime_type: str = "application/octet-stream"
    # When set, the attachment is embedded INLINE in the HTML at <img src="cid:{content_id}">
    content_id: Optional[str] = None
    inline: bool = False


@dataclass
class SendResult:
    status: str  # "sent" | "failed"
    error: Optional[str] = None


class EmailProvider(ABC):
    @abstractmethod
    async def send(
        self,
        to: str,
        subject: str,
        html: str,
        attachments: Optional[list[EmailAttachment]] = None,
    ) -> SendResult:
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass
