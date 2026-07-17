import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.llm.base import KnownCustomer, PlannerLLM, PlanningContext
from app.models.activity import ActivityType
from app.models.plan import Plan, PlanStep
from app.models.task import Task, TaskStatus
from app.services.activity_service import ActivityService
from app.services.crm_service import CRMService
from app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class PlanningError(Exception):
    pass


class PlannerService:
    """Turns a Task's raw request into a persisted Plan using the configured LLM."""

    def __init__(
        self,
        llm: PlannerLLM,
        tool_registry: ToolRegistry,
        activity_service: ActivityService,
        crm_service: CRMService,
        business_timezone: str,
    ) -> None:
        self._llm = llm
        self._tool_registry = tool_registry
        self._activity_service = activity_service
        self._crm_service = crm_service
        self._timezone = ZoneInfo(business_timezone)

    async def create_plan(self, session: AsyncSession, task: Task) -> Plan:
        task.status = TaskStatus.PLANNING
        await session.commit()
        await self._activity_service.emit(
            session,
            type=ActivityType.PLANNING_STARTED,
            message=f"Planning started for request: {task.raw_request[:120]}",
            task_id=task.id,
        )

        try:
            customers = await self._crm_service.list_customers()
            context = PlanningContext(
                request_text=task.raw_request,
                owner_phone=task.owner_phone,
                current_time=datetime.now(self._timezone),
                tools=self._tool_registry.specs(),
                known_customers=[
                    KnownCustomer(name=c.name, phone=c.phone, email=c.email) for c in customers
                ],
            )
            plan_result = await self._llm.generate_plan(context)
        except Exception as exc:  # noqa: BLE001
            task.status = TaskStatus.FAILED
            task.failure_reason = f"Planning failed: {exc}"
            await session.commit()
            await self._activity_service.emit(
                session,
                type=ActivityType.PLAN_FAILED,
                message=f"Planning failed: {exc}",
                task_id=task.id,
            )
            raise PlanningError(str(exc)) from exc

        unknown_tools = [
            step.tool for step in plan_result.steps if self._tool_registry.get(step.tool) is None
        ]
        if unknown_tools:
            task.status = TaskStatus.FAILED
            task.failure_reason = f"Plan referenced unknown tools: {unknown_tools}"
            await session.commit()
            await self._activity_service.emit(
                session,
                type=ActivityType.PLAN_FAILED,
                message=f"Plan referenced unknown tools: {unknown_tools}",
                task_id=task.id,
            )
            raise PlanningError(task.failure_reason)

        plan = Plan(
            task_id=task.id,
            model_used=getattr(self._llm, "_model", "unknown"),
            summary=plan_result.summary,
            raw_response=plan_result.model_dump(),
        )
        plan.steps = [
            PlanStep(
                step_number=index,
                tool_name=step.tool,
                tool_input=step.input,
                reasoning=step.reasoning,
            )
            for index, step in enumerate(plan_result.steps, start=1)
        ]

        task.status = TaskStatus.PLANNED
        session.add(plan)
        await session.commit()

        plan = (
            await session.execute(
                select(Plan).options(selectinload(Plan.steps)).where(Plan.id == plan.id)
            )
        ).scalar_one()

        await self._activity_service.emit(
            session,
            type=ActivityType.PLAN_CREATED,
            message=plan_result.summary,
            task_id=task.id,
            payload={"step_count": len(plan.steps)},
        )
        return plan
