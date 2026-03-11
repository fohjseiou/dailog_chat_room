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

    registry.register_tool(name="test_tool", tool_func=test_function)

    tools = registry.get_all_tools()
    assert "test_tool" in tools
    assert "search_cases" in tools  # Default tool


def test_get_tools_returns_default_initially():
    """Test that registry has default tools registered"""
    registry = ToolRegistry()  # Fresh instance
    # Default tools are auto-registered
    tools = registry.get_all_tools()
    assert "search_cases" in tools


def test_list_tools():
    """Test that list_tools returns tool names"""
    registry = ToolRegistry()
    tool_names = registry.list_tools()
    assert "search_cases" in tool_names
    assert isinstance(tool_names, list)
