"""Tool implementations for agent function calling."""
from typing import Dict, List
from app.agents.tools.case_search import search_cases

__all__ = ["search_cases", "ToolRegistry", "get_tool_registry"]


class ToolRegistry:
    """Registry for managing agent tools."""

    def __init__(self):
        self._tools: Dict[str, object] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Register default tools."""
        self.register_tool("search_cases", search_cases)

    def register_tool(self, name: str, tool_func: object):
        """Register a tool.

        Args:
            name: Tool name
            tool_func: Tool function (typically a LangChain tool)
        """
        self._tools[name] = tool_func

    def get_tool(self, name: str) -> object:
        """Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool function or None if not found
        """
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def get_all_tools(self) -> Dict[str, object]:
        """Get all registered tools.

        Returns:
            Dictionary mapping tool names to tool functions
        """
        return self._tools.copy()


_tool_registry: ToolRegistry = None


def get_tool_registry() -> ToolRegistry:
    """Get the singleton tool registry instance.

    Returns:
        ToolRegistry instance
    """
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry
