"""Starter tool adapters. Add new integrations by implementing ToolAdapter
and registering an instance in app.tools.setup.register_default_tools -- the
planner and executor never need to change.
"""

import logging

from app.services.whatsapp_service import WhatsAppService
from app.tools.base import ToolAdapter, ToolResult

logger = logging.getLogger(__name__)


class SendWhatsAppMessageTool(ToolAdapter):
    name = "send_whatsapp_message"
    description = "Send a WhatsApp text message back to the business owner."
    input_schema = {
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "Destination phone number in E.164 format."},
            "body": {"type": "string", "description": "Message text to send."},
        },
        "required": ["to", "body"],
    }

    def __init__(self, whatsapp_service: WhatsAppService) -> None:
        self._whatsapp_service = whatsapp_service

    async def execute(self, tool_input: dict) -> ToolResult:
        to = tool_input.get("to")
        body = tool_input.get("body")
        if not to or not body:
            return ToolResult(success=False, error="'to' and 'body' are required")

        try:
            response = await self._whatsapp_service.send_message(to=to, body=body)
        except Exception as exc:  # noqa: BLE001 - surfaced to caller as a failed step
            logger.exception("send_whatsapp_message failed")
            return ToolResult(success=False, error=str(exc))

        return ToolResult(success=True, output=response)


class CreateNoteTool(ToolAdapter):
    """Placeholder for a future notes/CRM integration -- demonstrates the
    adapter pattern for tools that don't need external credentials yet."""

    name = "create_note"
    description = "Record a short note about the task (placeholder for a notes/CRM integration)."
    input_schema = {
        "type": "object",
        "properties": {"note": {"type": "string"}},
        "required": ["note"],
    }

    async def execute(self, tool_input: dict) -> ToolResult:
        note = tool_input.get("note", "")
        logger.info("create_note: %s", note)
        return ToolResult(success=True, output={"note": note})


class WebSearchTool(ToolAdapter):
    """Stub -- wire up a real search provider (e.g. Brave, Tavily) later."""

    name = "web_search"
    description = "Search the web for information. Not yet connected to a real provider."
    input_schema = {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    }

    async def execute(self, tool_input: dict) -> ToolResult:
        query = tool_input.get("query", "")
        return ToolResult(
            success=False,
            error=f"web_search is not implemented yet (query was: {query!r})",
        )
