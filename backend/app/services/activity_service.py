import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import ActivityEvent, ActivityType


class ActivityService:
    """Persists activity events. The dashboard subscribes to this table
    directly via Supabase Realtime, so no in-process broadcast is needed --
    that also means this works unchanged on serverless (no WebSocket server
    to hold open)."""

    async def emit(
        self,
        session: AsyncSession,
        *,
        type: ActivityType,
        message: str,
        task_id: uuid.UUID | None = None,
        payload: dict[str, Any] | None = None,
    ) -> ActivityEvent:
        event = ActivityEvent(task_id=task_id, type=type, message=message, payload=payload)
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event
