import logging

from fastapi import APIRouter, Query, Request, Response, status

from app.core.config import get_settings
from app.core.deps import get_activity_service, get_orchestrator, get_whatsapp_service
from app.db.session import async_session_maker
from app.models.activity import ActivityType
from app.models.message import MessageDirection, WhatsAppMessage
from app.models.task import Task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook/whatsapp", tags=["whatsapp"])


@router.get("")
async def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> Response:
    challenge = get_whatsapp_service().verify_webhook(hub_mode, hub_verify_token, hub_challenge)
    if challenge is None:
        return Response(status_code=status.HTTP_403_FORBIDDEN)
    return Response(content=challenge, media_type="text/plain")


@router.post("")
async def receive_webhook(request: Request) -> dict:
    payload = await request.json()
    messages = get_whatsapp_service().parse_incoming(payload)

    # Awaited synchronously (not fire-and-forget) -- serverless functions
    # don't reliably keep running background tasks after the response is
    # sent, so the whole plan+execute pipeline has to finish within this
    # request. Keep the configured function timeout generous.
    async with async_session_maker() as session:
        activity_service = get_activity_service()
        for incoming in messages:
            task = Task(owner_phone=incoming.from_phone, raw_request=incoming.body)
            session.add(task)
            await session.flush()

            session.add(
                WhatsAppMessage(
                    task_id=task.id,
                    direction=MessageDirection.INBOUND,
                    phone=incoming.from_phone,
                    body=incoming.body,
                    wa_message_id=incoming.wa_message_id,
                )
            )
            await session.commit()

            await activity_service.emit(
                session,
                type=ActivityType.MESSAGE_RECEIVED,
                message=f"New request from {incoming.from_phone}: {incoming.body[:120]}",
                task_id=task.id,
            )

            await get_orchestrator().run(session, task)

    return {"status": "received", "count": len(messages)}


@router.get("/health")
async def whatsapp_config_health() -> dict:
    settings = get_settings()
    return {"configured": bool(settings.whatsapp_access_token and settings.whatsapp_phone_number_id)}
