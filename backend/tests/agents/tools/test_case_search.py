"""Tests for case search tool."""
import pytest
from app.agents.tools.case_search import search_cases


class TestCaseSearchTool:
    @pytest.mark.asyncio
    async def test_search_cases_returns_dict_with_cases_key(self):
        result = await search_cases.ainvoke({"query": "劳动合同纠纷"})
        assert isinstance(result, dict)
        assert "cases" in result

    @pytest.mark.asyncio
    async def test_search_cases_with_limit_parameter(self):
        result = await search_cases.ainvoke({"query": "test query", "limit": 3})
        assert len(result["cases"]) <= 3

    @pytest.mark.asyncio
    async def test_search_cases_handles_empty_query(self):
        result = await search_cases.ainvoke({"query": ""})
        assert "cases" in result
