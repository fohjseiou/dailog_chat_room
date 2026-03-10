"""Tests for ToolRegistry."""

import pytest
from app.agents.tools import ToolRegistry, get_tool_registry


def test_tool_registry_singleton():
    """Test that get_tool_registry returns singleton"""
    registry1 = get_tool_registry()
    registry2 = get_tool_registry()
    assert registry1 is registry2


def test_register_tool():
    """Test registering a new tool"""
    registry = get_tool_registry()

    def test_function(query: str) -> str:
        return f"Result for: {query}"

    registry.register(
        name="test_tool",
        func=test_function,
        description="A test tool"
    )

    tools = registry.get_tools()
    assert len(tools) == 1
    assert tools[0].name == "test_tool"


def test_get_tools_returns_empty_initially():
    """Test that get_tools returns empty list when no tools registered"""
    registry = ToolRegistry()  # Fresh instance
    tools = registry.get_tools()
    assert tools == []


def test_mcp_interface_exists():
    """Test that MCP integration interface is defined"""
    registry = ToolRegistry()
    assert hasattr(registry, 'load_from_mcp_server')
    # Implementation is TODO, but interface should exist
