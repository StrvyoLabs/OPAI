import asyncio
import logging
import smtplib
from abc import ABC, abstractmethod
from email.message import EmailMessage

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


class EmailConfigError(Exception):
    pass


class EmailService(ABC):
    @property
    @abstractmethod
    def sender_address(self) -> str | None:
        """The configured "from" address -- used to guard against a plan
        accidentally sending a customer's email to the business's own inbox."""
        ...

    @abstractmethod
    async def send(self, to: str, subject: str, html: str) -> dict: ...


class ResendEmailService(EmailService):
    """Thin client around the Resend email API.

    Resend requires DNS-verified domain ownership for the "from" address, so
    this can't send from a gmail.com/outlook.com/etc address -- use
    GmailSMTPEmailService for that instead.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def _configured(self) -> bool:
        return bool(self._settings.resend_api_key)

    @property
    def sender_address(self) -> str | None:
        return self._settings.resend_from_email

    async def send(self, to: str, subject: str, html: str) -> dict:
        if not self._configured:
            raise EmailConfigError("Resend is not configured (RESEND_API_KEY)")

        headers = {"Authorization": f"Bearer {self._settings.resend_api_key}"}
        payload = {
            "from": self._settings.resend_from_email,
            "to": [to],
            "subject": subject,
            "html": html,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(RESEND_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()


class GmailSMTPEmailService(EmailService):
    """Sends email via Gmail's SMTP server using an App Password.

    No custom domain required -- mail is sent from the Gmail address itself.
    Requires 2-Step Verification enabled on the Google account and an App
    Password generated at myaccount.google.com/apppasswords.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def _configured(self) -> bool:
        return bool(self._settings.gmail_address and self._settings.gmail_app_password)

    @property
    def sender_address(self) -> str | None:
        return self._settings.gmail_address

    def _send_sync(self, to: str, subject: str, html: str) -> None:
        message = EmailMessage()
        message["From"] = self._settings.gmail_address
        message["To"] = to
        message["Subject"] = subject
        message.set_content(html, subtype="html")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as smtp:
            smtp.login(self._settings.gmail_address, self._settings.gmail_app_password)
            smtp.send_message(message)

    async def send(self, to: str, subject: str, html: str) -> dict:
        if not self._configured:
            raise EmailConfigError("Gmail SMTP is not configured (GMAIL_ADDRESS / GMAIL_APP_PASSWORD)")

        await asyncio.to_thread(self._send_sync, to, subject, html)
        return {"provider": "gmail", "to": to}
