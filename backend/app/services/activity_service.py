import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ws_manager import ConnectionManager
from app.models.activity import ActivityEvent, ActivityType
from app.schemas.activity import ActivityEventRead


class ActivityService:
    """Persists activity events and fans them out to live dashboard clients."""

    def __init__(self, ws_manager: ConnectionManager) -> None:
        self._ws_manager = ws_manager

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

        await self._ws_manager.broadcast(
            {"event": "activity", "data": ActivityEventRead.model_validate(event).model_dump(mode="json")}
        )
        return event
