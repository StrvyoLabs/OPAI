import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_session
from app.models.plan import Plan
from app.models.task import Task
from app.schemas.task import TaskDetailRead, TaskRead

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
async def list_tasks(limit: int = 50, session: AsyncSession = Depends(get_session)) -> list[Task]:
    result = await session.execute(select(Task).order_by(Task.created_at.desc()).limit(limit))
    return list(result.scalars().all())


@router.get("/{task_id}", response_model=TaskDetailRead)
async def get_task(task_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> Task:
    result = await session.execute(
        select(Task)
        .options(selectinload(Task.plans).selectinload(Plan.steps))
        .where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
