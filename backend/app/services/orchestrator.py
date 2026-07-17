import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.services.executor_service import ExecutorService
from app.services.planner_service import PlannerService, PlanningError

logger = logging.getLogger(__name__)


class TaskOrchestrator:
    """Runs the plan-then-execute pipeline for a single Task end to end."""

    def __init__(self, planner_service: PlannerService, executor_service: ExecutorService) -> None:
        self._planner_service = planner_service
        self._executor_service = executor_service

    async def run(self, session: AsyncSession, task: Task) -> None:
        try:
            plan = await self._planner_service.create_plan(session, task)
        except PlanningError:
            logger.warning("Planning failed for task %s", task.id)
            return

        await self._executor_service.execute_plan(session, task, plan)
