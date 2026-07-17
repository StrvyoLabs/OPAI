from typing import Any

from pydantic import BaseModel, Field


class PlannedStep(BaseModel):
    """A single step in an LLM-generated execution plan, before it is persisted."""

    tool: str = Field(description="Name of the tool to invoke, must match a registered tool.")
    input: dict[str, Any] = Field(default_factory=dict, description="Arguments passed to the tool.")
    reasoning: str = Field(default="", description="Why this step is needed.")


class PlanResult(BaseModel):
    """Structured output the planner LLM must produce for a business request."""

    summary: str = Field(description="One or two sentence summary of the overall plan.")
    steps: list[PlannedStep] = Field(default_factory=list)


PLAN_RESULT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "tool": {"type": "string"},
                    "input": {"type": "object"},
                    "reasoning": {"type": "string"},
                },
                "required": ["tool", "input", "reasoning"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["summary", "steps"],
    "additionalProperties": False,
}
