from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_activity_service, get_orchestrator
from app.db.session import get_session
from app.models.activity import ActivityType
from app.models.task import Task
from app.schemas.task import CreateTaskRequest, TaskRead

router = APIRouter(prefix="/planner", tags=["planner"])


@router.post("/plan", response_model=TaskRead)
async def plan_request(body: CreateTaskRequest, session: AsyncSession = Depends(get_session)) -> Task:
    """Manually trigger a task + plan without going through WhatsApp. Handy
    for testing the planner/executor pipeline from the dashboard or curl.

    Awaited synchronously (not fire-and-forget) so it works the same way on
    serverless as the WhatsApp webhook does -- the response only returns
    once the full plan+execute pipeline has finished.
    """

    task = Task(owner_phone=body.owner_phone, raw_request=body.raw_request)
    session.add(task)
    await session.commit()
    await session.refresh(task)

    await get_activity_service().emit(
        session,
        type=ActivityType.MESSAGE_RECEIVED,
        message=f"New request from {body.owner_phone}: {body.raw_request[:120]}",
        task_id=task.id,
    )

    await get_orchestrator().run(session, task)
    await session.refresh(task)
    return task
