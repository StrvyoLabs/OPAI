from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolSpec:
    """Describes a tool to the planner LLM so it knows what it can call."""

    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    success: bool
    output: Any = None
    error: str | None = None


class ToolAdapter(ABC):
    """Base interface every integration/tool must implement.

    Keeping every integration behind this interface is what lets new tools
    (calendar, CRM, email, payments, ...) be added later without touching the
    planner or executor.
    """

    name: str
    description: str
    input_schema: dict[str, Any] = {}

    def spec(self) -> ToolSpec:
        return ToolSpec(name=self.name, description=self.description, input_schema=self.input_schema)

    @abstractmethod
    async def execute(self, tool_input: dict[str, Any]) -> ToolResult: ...
