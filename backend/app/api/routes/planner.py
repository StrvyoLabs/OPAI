import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_activity_service, get_orchestrator
from app.db.session import async_session_maker, get_session
from app.models.activity import ActivityType
from app.models.task import Task
from app.schemas.task import CreateTaskRequest, TaskRead

router = APIRouter(prefix="/planner", tags=["planner"])


async def _run_task(task_id) -> None:
    async with async_session_maker() as session:
        task = await session.get(Task, task_id)
        if task is not None:
            await get_orchestrator().run(session, task)


@router.post("/plan", response_model=TaskRead)
async def plan_request(body: CreateTaskRequest, session: AsyncSession = Depends(get_session)) -> Task:
    """Manually trigger a task + plan without going through WhatsApp. Handy
    for testing the planner/executor pipeline from the dashboard or curl."""

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

    asyncio.create_task(_run_task(task.id))
    return task
