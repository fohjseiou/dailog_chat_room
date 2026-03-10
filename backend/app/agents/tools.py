"""Tool registry for agent function calling.

This module provides a centralized tool registry that can be extended
to support MCP (Model Context Protocol) servers in the future.
"""

from typing import Dict, List, Callable, Any
from langchain_core.tools import Tool
import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry for managing tools available to the agent.

    This class provides a foundation for tool management and includes
    placeholder methods for future MCP server integration.
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(
        self,
        name: str,
        func: Callable,
        description: str
    ) -> None:
        """
        Register a new tool.

        Args:
            name: Unique identifier for the tool
            func: Callable that implements the tool functionality
            description: Human-readable description of what the tool does
        """
        self._tools[name] = Tool(
            name=name,
            func=func,
            description=description
        )
        logger.info(f"Registered tool: {name}")

    def get_tools(self) -> List[Tool]:
        """
        Get all registered tools.

        Returns:
            List of all registered Tool objects
        """
        return list(self._tools.values())

    async def load_from_mcp_server(self, server_url: str) -> None:
        """
        Load tools from an MCP server.

        This is a placeholder for future MCP protocol integration.
        When implemented, this will connect to an MCP server and
        dynamically register tools provided by that server.

        Args:
            server_url: URL of the MCP server to connect to

        Raises:
            NotImplementedError: This method is not yet implemented
        """
        raise NotImplementedError(
            "MCP server integration is not yet implemented. "
            "This is a placeholder for future functionality."
        )


# Global singleton instance
_tool_registry: ToolRegistry = None


def get_tool_registry() -> ToolRegistry:
    """
    Get or create the global ToolRegistry singleton.

    Returns:
        The global ToolRegistry instance
    """
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry
