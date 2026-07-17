from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from app.schemas.plan import PlanResult
from app.tools.base import ToolSpec


@dataclass
class KnownCustomer:
    name: str
    phone: str | None
    email: str | None


@dataclass
class PlanningContext:
    request_text: str
    owner_phone: str
    current_time: datetime
    tools: list[ToolSpec]
    known_customers: list[KnownCustomer] = field(default_factory=list)


class PlannerLLM(ABC):
    """Interface for whatever model turns a natural-language request into a
    structured execution plan. Swapping planner models means implementing
    this interface, not touching the planner/executor services.
    """

    @abstractmethod
    async def generate_plan(self, context: PlanningContext) -> PlanResult: ...

    @abstractmethod
    async def compose_reply(self, request_text: str, completed_steps: list[dict]) -> str:
        """Writes the actual WhatsApp reply text after prior steps have run,
        using their real results -- the plan's own drafted body is written
        before those results exist and often can't know the answer yet
        (e.g. "when is X's appointment" needs find_customer's result first).
        """
        ...
