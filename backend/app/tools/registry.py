from app.tools.base import ToolAdapter, ToolSpec


class ToolRegistry:
    """Central lookup for every ToolAdapter available to the planner/executor."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolAdapter] = {}

    def register(self, tool: ToolAdapter) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolAdapter | None:
        return self._tools.get(name)

    def specs(self) -> list[ToolSpec]:
        return [tool.spec() for tool in self._tools.values()]

    def names(self) -> list[str]:
        return list(self._tools.keys())


tool_registry = ToolRegistry()
