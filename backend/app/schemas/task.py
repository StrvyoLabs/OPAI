import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.plan import PlanStepStatus
from app.models.task import TaskStatus


class PlanStepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    step_number: int
    tool_name: str
    tool_input: dict[str, Any]
    reasoning: str | None
    status: PlanStepStatus
    result: dict[str, Any] | None
    error: str | None


class PlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    model_used: str
    summary: str | None
    created_at: datetime
    steps: list[PlanStepRead] = []


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_phone: str
    raw_request: str
    status: TaskStatus
    failure_reason: str | None
    created_at: datetime
    updated_at: datetime


class TaskDetailRead(TaskRead):
    plans: list[PlanRead] = []


class CreateTaskRequest(BaseModel):
    owner_phone: str
    raw_request: str
