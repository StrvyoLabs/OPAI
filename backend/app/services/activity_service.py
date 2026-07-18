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
        # No refresh needed: id/created_at/updated_at are all set client-side
        # (see UUIDPKMixin/TimestampMixin) and the session has
        # expire_on_commit=False, so this object's fields are already
        # correct post-commit without another round-trip to reload them.
        event = ActivityEvent(task_id=task_id, type=type, message=message, payload=payload)
        session.add(event)
        await session.commit()
        return event
