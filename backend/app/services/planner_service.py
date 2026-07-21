import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.llm.base import ConversationTurn, KnownCustomer, PlannerLLM, PlanningContext
from app.models.activity import ActivityType
from app.models.plan import Plan, PlanStep, PlanStepStatus
from app.models.task import Task, TaskStatus
from app.services.activity_service import ActivityService
from app.services.crm_service import CRMService
from app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

RECENT_CONVERSATION_LIMIT = 6


class PlanningError(Exception):
    pass


class PlannerService:
    """Turns a Task's raw request into a persisted Plan using the configured LLM.

    Status changes are set on the Task/Plan ORM objects but not committed on
    their own -- ActivityService.emit() commits the whole session, so a
    status change staged right before the matching emit() persists both in
    one round-trip. Each round-trip is expensive from a serverless function,
    so halving the commit count roughly halves total request latency.
    """

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
        await self._activity_service.emit(
            session,
            type=ActivityType.PLANNING_STARTED,
            message=f"Planning started for request: {task.raw_request[:120]}",
            task_id=task.id,
        )

        try:
            t0 = time.monotonic()
            customers = await self._crm_service.list_customers()
            recent_conversation = await self._recent_conversation(session, task)
            t1 = time.monotonic()
            logger.info("TIMING list_customers+recent_conversation: %.2fs", t1 - t0)
            context = PlanningContext(
                request_text=task.raw_request,
                owner_phone=task.owner_phone,
                current_time=datetime.now(self._timezone),
                tools=self._tool_registry.specs(),
                known_customers=[
                    KnownCustomer(name=c.name, phone=c.phone, email=c.email) for c in customers
                ],
                recent_conversation=recent_conversation,
            )
            plan_result = await self._llm.generate_plan(context)
            t2 = time.monotonic()
            logger.info("TIMING generate_plan (Groq call): %.2fs", t2 - t1)
        except Exception as exc:  # noqa: BLE001
            task.status = TaskStatus.FAILED
            task.failure_reason = f"Planning failed: {exc}"
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

        # No re-query needed: plan.steps was just built in Python above, so
        # the object already has everything the caller needs. (A prior
        # version re-queried here, but doing so before any flush meant
        # `plan.id` was still None -- read as a plain Python attribute
        # access at expression-build time, before autoflush could populate
        # it -- so the query silently matched nothing.)
        await self._activity_service.emit(
            session,
            type=ActivityType.PLAN_CREATED,
            message=plan_result.summary,
            task_id=task.id,
            payload={"step_count": len(plan.steps)},
        )
        return plan

    async def _recent_conversation(self, session: AsyncSession, task: Task) -> list[ConversationTurn]:
        """Loads the owner's last few finished requests (and how they were
        answered) so the planner can resolve vague references like "it" or
        "that customer" to whatever was actually being discussed, instead of
        having to treat every message as a blank slate."""

        result = await session.execute(
            select(Task)
            .where(
                Task.owner_phone == task.owner_phone,
                Task.id != task.id,
                Task.status.in_([TaskStatus.COMPLETED, TaskStatus.COMPLETED_WITH_ERRORS]),
            )
            .options(selectinload(Task.plans).selectinload(Plan.steps))
            .order_by(Task.created_at.desc())
            .limit(RECENT_CONVERSATION_LIMIT)
        )
        recent_tasks = list(result.scalars().all())
        recent_tasks.reverse()  # oldest first, so the transcript reads chronologically

        turns: list[ConversationTurn] = []
        for recent_task in recent_tasks:
            if not recent_task.plans:
                continue
            latest_plan = max(recent_task.plans, key=lambda p: p.created_at)
            reply_text = latest_plan.summary
            for step in latest_plan.steps:
                if step.tool_name == "send_whatsapp_message" and step.status == PlanStepStatus.SUCCEEDED:
                    reply_text = step.tool_input.get("body", reply_text)
            turns.append(
                ConversationTurn(
                    request_text=recent_task.raw_request,
                    reply_text=reply_text,
                    created_at=recent_task.created_at,
                )
            )
        return turns
