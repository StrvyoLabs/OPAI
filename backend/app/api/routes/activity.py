from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.activity import ActivityEvent
from app.schemas.activity import ActivityEventRead

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("", response_model=list[ActivityEventRead])
async def list_activity(limit: int = 50, session: AsyncSession = Depends(get_session)) -> list[ActivityEvent]:
    result = await session.execute(
        select(ActivityEvent).order_by(ActivityEvent.created_at.desc()).limit(limit)
    )
    events = list(result.scalars().all())
    events.reverse()
    return events
