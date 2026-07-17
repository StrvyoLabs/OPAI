import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class IncomingWhatsAppMessage:
    from_phone: str
    body: str
    wa_message_id: str


class WhatsAppService:
    """Thin client around the Meta WhatsApp Business Cloud API."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def verify_webhook(self, mode: str | None, token: str | None, challenge: str | None) -> str | None:
        if mode == "subscribe" and token == self._settings.whatsapp_verify_token and challenge:
            return challenge
        return None

    @staticmethod
    def parse_incoming(payload: dict[str, Any]) -> list[IncomingWhatsAppMessage]:
        messages: list[IncomingWhatsAppMessage] = []
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for message in value.get("messages", []):
                    if message.get("type") != "text":
                        continue
                    messages.append(
                        IncomingWhatsAppMessage(
                            from_phone=message.get("from", ""),
                            body=message.get("text", {}).get("body", ""),
                            wa_message_id=message.get("id", ""),
                        )
                    )
        return messages

    async def send_message(self, to: str, body: str) -> dict[str, Any]:
        if not self._settings.whatsapp_access_token or not self._settings.whatsapp_phone_number_id:
            logger.warning("WhatsApp credentials not configured; skipping send to %s: %s", to, body)
            return {"skipped": True}

        headers = {"Authorization": f"Bearer {self._settings.whatsapp_access_token}"}
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body},
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(self._settings.whatsapp_graph_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
