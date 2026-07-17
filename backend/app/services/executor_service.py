import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.base import PlannerLLM
from app.models.activity import ActivityType
from app.models.plan import Plan, PlanStep, PlanStepStatus
from app.models.task import Task, TaskStatus
from app.services.activity_service import ActivityService
from app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class ExecutorService:
    """Runs a Plan's steps in order against the registered tool adapters.

    Steps are independent by default: if one fails, the rest still run --
    a missing customer email shouldn't block an otherwise-unrelated calendar
    booking. The task's final status reflects whether any step failed.
    """

    def __init__(self, tool_registry: ToolRegistry, activity_service: ActivityService, reply_llm: PlannerLLM) -> None:
        self._tool_registry = tool_registry
        self._activity_service = activity_service
        self._reply_llm = reply_llm

    async def execute_plan(self, session: AsyncSession, task: Task, plan: Plan) -> None:
        task.status = TaskStatus.EXECUTING
        await session.commit()

        any_failed = False

        for index, step in enumerate(plan.steps):
            preceding_steps = plan.steps[:index]
            if step.tool_name == "send_whatsapp_message" and preceding_steps:
                await self._recompose_reply(task, step, preceding_steps)

            step.status = PlanStepStatus.RUNNING
            await session.commit()
            await self._activity_service.emit(
                session,
                type=ActivityType.STEP_STARTED,
                message=f"Running step {step.step_number}: {step.tool_name}",
                task_id=task.id,
                payload={"step_id": str(step.id), "tool": step.tool_name, "input": step.tool_input},
            )

            tool = self._tool_registry.get(step.tool_name)
            if tool is None:
                any_failed = True
                step.status = PlanStepStatus.FAILED
                step.error = f"Unknown tool: {step.tool_name}"
                await session.commit()
                await self._activity_service.emit(
                    session,
                    type=ActivityType.STEP_FAILED,
                    message=f"Step {step.step_number} ({step.tool_name}) failed: {step.error}",
                    task_id=task.id,
                    payload={"step_id": str(step.id), "error": step.error},
                )
                continue

            result = await tool.execute(step.tool_input)

            if result.success:
                step.status = PlanStepStatus.SUCCEEDED
                step.result = result.output if isinstance(result.output, dict) else {"value": result.output}
                await session.commit()
                await self._activity_service.emit(
                    session,
                    type=ActivityType.STEP_SUCCEEDED,
                    message=f"Step {step.step_number} ({step.tool_name}) succeeded",
                    task_id=task.id,
                    payload={"step_id": str(step.id), "result": step.result},
                )
            else:
                any_failed = True
                step.status = PlanStepStatus.FAILED
                step.error = result.error
                await session.commit()
                await self._activity_service.emit(
                    session,
                    type=ActivityType.STEP_FAILED,
                    message=f"Step {step.step_number} ({step.tool_name}) failed: {result.error}",
                    task_id=task.id,
                    payload={"step_id": str(step.id), "error": result.error},
                )

        if any_failed:
            failed_steps = [s for s in plan.steps if s.status == PlanStepStatus.FAILED]
            if len(failed_steps) == len(plan.steps):
                await self._fail_task(session, task, "All steps failed")
            else:
                task.status = TaskStatus.COMPLETED_WITH_ERRORS
                task.failure_reason = "; ".join(
                    f"Step {s.step_number} ({s.tool_name}): {s.error}" for s in failed_steps
                )
                await session.commit()
                await self._activity_service.emit(
                    session,
                    type=ActivityType.TASK_COMPLETED,
                    message="Task completed with some steps failing",
                    task_id=task.id,
                )
            return

        task.status = TaskStatus.COMPLETED
        await session.commit()
        await self._activity_service.emit(
            session,
            type=ActivityType.TASK_COMPLETED,
            message="Task completed successfully",
            task_id=task.id,
        )

    async def _recompose_reply(self, task: Task, step: PlanStep, preceding_steps: list[PlanStep]) -> None:
        """Rewrites a WhatsApp reply step's body using the real results of the
        steps that already ran, since the plan drafted it before those
        results existed and can't reliably know the answer yet."""

        completed = [
            {
                "step": s.step_number,
                "tool": s.tool_name,
                "status": s.status.value,
                "result": s.result,
                "error": s.error,
            }
            for s in preceding_steps
        ]
        try:
            body = await self._reply_llm.compose_reply(task.raw_request, completed)
            step.tool_input = {**step.tool_input, "body": body}
        except Exception:  # noqa: BLE001 - fall back to the plan's original drafted body
            logger.exception("Failed to recompose WhatsApp reply for step %s; using drafted body", step.id)

    async def _fail_task(self, session: AsyncSession, task: Task, reason: str) -> None:
        task.status = TaskStatus.FAILED
        task.failure_reason = reason
        await session.commit()
        await self._activity_service.emit(
            session,
            type=ActivityType.TASK_FAILED,
            message=f"Task failed: {reason}",
            task_id=task.id,
        )
