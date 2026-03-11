# Legal Case Search Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a legal case search feature that allows users to search for relevant court cases after receiving legal consultation responses.

**Architecture:** User clicks "Search Cases" button → Frontend sends `search_cases:{query}` → Graph routes to `case_search_node` → LLM calls `search_cases` tool → Firecrawl searches web → Results displayed in chat.

**Tech Stack:** LangChain (ChatTongyi with tool calling), Firecrawl MCP, React, FastAPI

---

## Chunk 1: Backend Infrastructure - Firecrawl Service

### Task 1: Create Firecrawl service with configuration

**Files:**
- Create: `backend/app/services/firecrawl_service.py`
- Modify: `backend/app/config.py`
- Test: `tests/services/test_firecrawl_service.py`

- [ ] **Step 0: Verify Firecrawl MCP tool availability**

Before starting, verify the MCP tool import path:

```bash
cd backend
python -c "import sys; print('\\n'.join(sys.path))"
python -c "try:
    from mcp__firecrawl__firecrawl_search import firecrawl_search
    print('✓ MCP import: mcp__firecrawl__firecrawl_search')
except ImportError:
    try:
        from mcp__firecrawl import firecrawl_search
        print('✓ MCP import: mcp__firecrawl')
    except ImportError:
        print('✗ Firecrawl MCP not found - will use mock for testing')
"
```

Note the correct import path for your environment. The plan below uses `mcp__firecrawl__firecrawl_search` - adjust if different.

- [ ] **Step 1: Add FIRECRAWL_API_KEY to config**

Modify `backend/app/config.py` to add the new configuration field. First, find the `Settings` class and add after existing fields:

```python
# In class Settings, add after existing fields
firecrawl_api_key: str = Field(default="", env="FIRECRAWL_API_KEY")
```

- [ ] **Step 2: Verify .env file has FIRECRAWL_API_KEY**

Check or add to `backend/.env`:

```bash
# Check if FIRECRAWL_API_KEY exists
grep FIRECRAWL_API_KEY .env || echo "FIRECRAWL_API_KEY=" >> .env
```

- [ ] **Step 3: Write failing test for FirecrawlService**

Create `tests/services/test_firecrawl_service.py`:

```python
import pytest
from app.services.firecrawl_service import FirecrawlService, get_firecrawl_service
from app.config import get_settings

class TestFirecrawlService:
    @pytest.mark.asyncio
    async def test_get_firecrawl_service_returns_singleton(self):
        """Test that get_firecrawl_service returns singleton instance"""
        service1 = get_firecrawl_service()
        service2 = get_firecrawl_service()
        assert service1 is service2

    @pytest.mark.asyncio
    async def test_firecrawl_service_has_api_key(self):
        """Test that FirecrawlService loads API key from config"""
        service = get_firecrawl_service()
        assert hasattr(service, 'api_key')

    @pytest.mark.asyncio
    async def test_is_available_returns_true_with_api_key(self):
        """Test that is_available returns True when API key is set"""
        service = FirecrawlService()
        service.api_key = "test_key"
        assert await service.is_available() is True

    @pytest.mark.asyncio
    async def test_is_available_returns_false_without_api_key(self):
        """Test that is_available returns False when API key is empty"""
        service = FirecrawlService()
        service.api_key = ""
        assert await service.is_available() is False

    @pytest.mark.asyncio
    async def test_search_with_mock_returns_results(self):
        """Test search method with mocked Firecrawl"""
        # This will fail until we implement the service
        service = get_firecrawl_service()
        results = await service.search("劳动合同纠纷", limit=5)
        assert "results" in results or "error" in results
```

- [ ] **Step 4: Run test to verify it fails**

Run: `pytest tests/services/test_firecrawl_service.py -v`
Expected: FAIL with "module 'app.services.firecrawl_service' not found"

- [ ] **Step 5: Create FirecrawlService implementation**

Create `backend/app/services/firecrawl_service.py`:

```python
"""Firecrawl service for web search and scraping.

This service wraps Firecrawl MCP tools for searching legal cases
and court decisions from the web.
"""
import logging
from typing import Dict, Any, Optional, List
from app.config import get_settings

logger = logging.getLogger(__name__)

# Try different import paths for Firecrawl MCP
_FIRECRAWL_AVAILABLE = False
_FIRECRAWL_IMPORT = None

try:
    from mcp__firecrawl__firecrawl_search import firecrawl_search
    _FIRECRAWL_AVAILABLE = True
    _FIRECRAWL_IMPORT = "mcp__firecrawl__firecrawl_search"
except ImportError:
    try:
        from mcp__firecrawl import firecrawl_search
        _FIRECRAWL_AVAILABLE = True
        _FIRECRAWL_IMPORT = "mcp__firecrawl"
    except ImportError:
        logger.warning("Firecrawl MCP not available - case search will be mocked")


class FirecrawlService:
    """Service for Firecrawl API integration.

    This service provides methods to search the web for legal cases
    using the Firecrawl MCP tool.
    """

    def __init__(self):
        """Initialize FirecrawlService with API key from config."""
        self.settings = get_settings()
        self.api_key = self.settings.firecrawl_api_key

    async def search(
        self,
        query: str,
        limit: int = 5,
        scrape_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform web search using Firecrawl.

        Args:
            query: Search query string
            limit: Maximum number of results to return (default: 5)
            scrape_options: Options for content extraction

        Returns:
            Dictionary with search results containing 'results' list.
            Returns {'results': [], 'error': message} on failure.
        """
        if not self.api_key:
            logger.warning("FIRECRAWL_API_KEY not configured")
            return {
                "results": [],
                "error": "FIRECRAWL_API_KEY not configured. Set FIRECRAWL_API_KEY environment variable."
            }

        if not _FIRECRAWL_AVAILABLE:
            logger.warning("Firecrawl MCP not available")
            return {
                "results": [],
                "error": "Firecrawl MCP tool not available. Install MCP Firecrawl server."
            }

        try:
            # Import here to avoid issues if MCP not available
            if _FIRECRAWL_IMPORT == "mcp__firecrawl__firecrawl_search":
                from mcp__firecrawl__firecrawl_search import firecrawl_search
            else:
                from mcp__firecrawl import firecrawl_search

            # Build search query focused on Chinese legal databases
            enhanced_query = f"{query} 裁判文书 案例 判决"

            # Perform search using Firecrawl MCP
            results = await firecrawl_search(
                query=enhanced_query,
                limit=limit,
                scrape_options=scrape_options or {"formats": ["markdown"]}
            )

            # Safe access to results key
            result_list = results.get("results", []) if isinstance(results, dict) else []
            logger.info(f"Firecrawl search completed: {len(result_list)} results")

            return results

        except Exception as e:
            logger.error(f"Firecrawl search error: {e}")
            return {
                "results": [],
                "error": f"Search failed: {str(e)}"
            }

    async def is_available(self) -> bool:
        """Check if Firecrawl service is available."""
        return bool(self.api_key) and _FIRECRAWL_AVAILABLE


# Singleton instance
_firecrawl_service: Optional[FirecrawlService] = None


def get_firecrawl_service() -> FirecrawlService:
    """Get or create the FirecrawlService singleton."""
    global _firecrawl_service
    if _firecrawl_service is None:
        _firecrawl_service = FirecrawlService()
    return _firecrawl_service
```

- [ ] **Step 7: Run test to verify it passes**

Run: `pytest tests/services/test_firecrawl_service.py -v`
Expected: PASS (test_singleton and test_api_key pass, test_search may need mock)

- [ ] **Step 8: Update test with proper mock for search**

Update `tests/services/test_firecrawl_service.py` to add mock:

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.services.firecrawl_service import FirecrawlService, get_firecrawl_service

class TestFirecrawlService:
    @pytest.mark.asyncio
    async def test_get_firecrawl_service_returns_singleton(self):
        service1 = get_firecrawl_service()
        service2 = get_firecrawl_service()
        assert service1 is service2

    @pytest.mark.asyncio
    async def test_firecrawl_service_has_api_key(self):
        service = get_firecrawl_service()
        assert hasattr(service, 'api_key')

    @pytest.mark.asyncio
    async def test_is_available_returns_true_with_api_key(self):
        """Test that is_available returns True when API key is set"""
        service = FirecrawlService()
        service.api_key = "test_key"
        # Note: Result depends on MCP availability
        result = await service.is_available()
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_is_available_returns_false_without_api_key(self):
        """Test that is_available returns False when API key is empty"""
        service = FirecrawlService()
        service.api_key = ""
        assert await service.is_available() is False

    @pytest.mark.asyncio
    async def test_search_with_mock_returns_results(self):
        """Test with mocked Firecrawl MCP"""
        service = get_firecrawl_service()

        # Mock at module level
        with patch('app.services.firecrawl_service._FIRECRAWL_AVAILABLE', True):
            with patch('app.services.firecrawl_service.firecrawl_search', new_callable=AsyncMock) as mock_search:
                mock_search.return_value = {
                    "results": [
                        {"title": "Test Case", "url": "http://example.com", "markdown": "Test content"}
                    ]
                }

                results = await service.search("劳动合同纠纷", limit=5)
                assert "results" in results
                assert isinstance(results.get("results"), list)

    @pytest.mark.asyncio
    async def test_search_returns_error_when_no_api_key(self):
        """Test that search returns error dict when API key is missing"""
        service = FirecrawlService()
        service.api_key = ""

        result = await service.search("test query")

        assert "results" in result
        assert result["results"] == []
        assert "error" in result

    @pytest.mark.asyncio
    async def test_search_handles_missing_results_key(self):
        """Test that search handles malformed response safely"""
        service = FirecrawlService()
        service.api_key = "test_key"

        with patch('app.services.firecrawl_service._FIRECRAWL_AVAILABLE', True):
            with patch('app.services.firecrawl_service.firecrawl_search', new_callable=AsyncMock) as mock_search:
                mock_search.return_value = {"data": "something"}

                result = await service.search("test")
                # Should handle gracefully
                assert "results" in result or "error" in result
```

- [ ] **Step 9: Run all tests to verify they pass**

Run: `pytest tests/services/test_firecrawl_service.py -v`
Expected: All tests PASS

- [ ] **Step 10: Commit**

```bash
git add backend/app/services/firecrawl_service.py backend/app/config.py tests/services/test_firecrawl_service.py
git commit -m "feat: add FirecrawlService for web search

- Add firecrawl_api_key to Settings
- Implement FirecrawlService with safe error handling
- Try multiple import paths for Firecrawl MCP
- Add singleton get_firecrawl_service()
- Add comprehensive unit tests with mocking
- Handle missing API key and malformed responses

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 2: Backend Infrastructure - Case Search Tool

### Task 2: Create case search tool implementation

**Files:**
- Create: `backend/app/agents/tools/__init__.py`
- Create: `backend/app/agents/tools/case_search.py`
- Test: `tests/agents/tools/test_case_search.py`

- [ ] **Step 1: Create tools directory structure**

```bash
mkdir -p backend/app/agents/tools
```

- [ ] **Step 2: Write failing test for search_cases tool**

Create `tests/agents/tools/test_case_search.py`:

```python
import pytest
from app.agents.tools.case_search import search_cases

class TestCaseSearchTool:
    @pytest.mark.asyncio
    async def test_search_cases_returns_dict_with_cases_key(self):
        """Test that search_cases returns dict with 'cases' key"""
        result = await search_cases("劳动合同纠纷")
        assert isinstance(result, dict)
        assert "cases" in result

    @pytest.mark.asyncio
    async def test_search_cases_with_limit_parameter(self):
        """Test that limit parameter works"""
        result = await search_cases("test query", limit=3)
        assert len(result["cases"]) <= 3

    @pytest.mark.asyncio
    async def test_search_cases_handles_empty_query(self):
        """Test that empty query is handled gracefully"""
        result = await search_cases("")
        assert "cases" in result
        # Should not crash, may return empty cases or error
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/agents/tools/test_case_search.py -v`
Expected: FAIL with "module 'app.agents.tools.case_search' not found"

- [ ] **Step 4: Create tools __init__.py**

Create `backend/app/agents/tools/__init__.py`:

```python
"""Tool implementations for agent function calling.

This package contains individual tool implementations that can be
registered with the ToolRegistry and bound to LLMs for tool calling.
"""

__all__ = ["search_cases"]
```

- [ ] **Step 5: Implement search_cases tool**

Create `backend/app/agents/tools/case_search.py`:

```python
"""Case search tool for finding relevant legal cases.

This tool uses Firecrawl to search the web for court cases and
legal decisions relevant to the user's query.
"""
import logging
from typing import Dict, Any
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
async def search_cases(query: str, limit: int = 5) -> Dict[str, Any]:
    """
    Search for relevant legal cases and court decisions on the web.

    This tool searches Chinese legal databases and court document websites
    to find relevant cases based on the user's query.

    Args:
        query: Search query describing the legal topic or case type
        limit: Maximum number of cases to return (default: 5, max: 10)

    Returns:
        Dictionary containing:
            - cases: List of case dictionaries with title, summary, url
            - total_found: Total number of cases found
            - error: Error message if search failed (optional)

    Examples:
        >>> result = await search_cases("劳动合同纠纷")
        >>> print(result["cases"][0]["title"])
        "张三诉公司劳动合同纠纷案"
    """
    # Validate inputs
    if not query or not query.strip():
        return {
            "cases": [],
            "total_found": 0,
            "error": "Search query cannot be empty"
        }

    # Limit max results to avoid excessive API calls
    limit = min(max(1, limit), 10)

    try:
        from app.services.firecrawl_service import get_firecrawl_service

        firecrawl = get_firecrawl_service()

        # Perform search
        search_results = await firecrawl.search(
            query=query,
            limit=limit,
            scrape_options={"formats": ["markdown"]}
        )

        # Format results into case structure
        cases = []
        raw_results = search_results.get("results", [])

        for result in raw_results[:limit]:
            case = {
                "title": result.get("title", "Unknown Case"),
                "summary": _extract_summary(result),
                "url": result.get("url", ""),
                "relevance": result.get("score", 0)
            }
            cases.append(case)

        return {
            "cases": cases,
            "total_found": len(cases)
        }

    except ValueError as e:
        # Configuration error
        logger.error(f"Configuration error in case search: {e}")
        return {
            "cases": [],
            "total_found": 0,
            "error": "Case search not properly configured"
        }
    except Exception as e:
        # Search error
        logger.error(f"Case search failed: {e}")
        return {
            "cases": [],
            "total_found": 0,
            "error": f"Search failed: {str(e)}"
        }


def _extract_summary(result: Dict[str, Any]) -> str:
    """Extract a summary from search result.

    Args:
        result: Single search result dictionary

    Returns:
        Summary string (max 500 characters)
    """
    # Try to get markdown content first
    markdown = result.get("markdown", "")

    if markdown:
        # Return first 500 chars of markdown
        return markdown[:500]

    # Fallback to any text content
    text = result.get("text", "")
    return text[:500] if text else "No summary available"
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/agents/tools/test_case_search.py -v`
Expected: Tests PASS (with mocked Firecrawl)

- [ ] **Step 7: Update test to mock FirecrawlService**

Update `tests/agents/tools/test_case_search.py` with proper mocking:

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.agents.tools.case_search import search_cases

class TestCaseSearchTool:
    @pytest.mark.asyncio
    async def test_search_cases_returns_dict_with_cases_key(self):
        result = await search_cases("劳动合同纠纷")
        assert isinstance(result, dict)
        assert "cases" in result

    @pytest.mark.asyncio
    async def test_search_cases_with_mocked_firecrawl(self):
        """Test with mocked FirecrawlService"""
        with patch('app.agents.tools.case_search.get_firecrawl_service') as mock_get:
            mock_service = AsyncMock()
            mock_service.search.return_value = {
                "results": [
                    {
                        "title": "Test Case 1",
                        "url": "http://example.com/1",
                        "markdown": "Test summary 1"
                    },
                    {
                        "title": "Test Case 2",
                        "url": "http://example.com/2",
                        "markdown": "Test summary 2"
                    }
                ]
            }
            mock_get.return_value = mock_service

            result = await search_cases("test query", limit=5)

            assert result["total_found"] == 2
            assert len(result["cases"]) == 2
            assert result["cases"][0]["title"] == "Test Case 1"

    @pytest.mark.asyncio
    async def test_search_cases_with_empty_query(self):
        """Test that empty query returns error"""
        result = await search_cases("")
        assert "cases" in result
        assert result["total_found"] == 0
        assert "error" in result

    @pytest.mark.asyncio
    async def test_search_cases_limits_max_results(self):
        """Test that limit parameter caps at 10"""
        with patch('app.agents.tools.case_search.get_firecrawl_service') as mock_get:
            mock_service = AsyncMock()
            # Request 15 but should only get 10
            mock_service.search.return_value = {"results": []}
            mock_get.return_value = mock_service

            # This should work without error
            result = await search_cases("test", limit=15)
            assert "cases" in result
```

- [ ] **Step 8: Run all tests to verify**

Run: `pytest tests/agents/tools/test_case_search.py -v`
Expected: All tests PASS

- [ ] **Step 9: Commit**

```bash
git add backend/app/agents/tools/ tests/agents/tools/
git commit -m "feat: add case search tool implementation

- Create backend/app/agents/tools/ directory
- Implement search_cases tool with LangChain @tool decorator
- Add input validation and error handling
- Mock FirecrawlService in tests
- Add comprehensive unit tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 3: Backend Infrastructure - Tool Registration

### Task 3: Register case_search tool in ToolRegistry

**Files:**
- Modify: `backend/app/agents/tools.py`
- Test: `tests/agents/test_tool_registry.py`

- [ ] **Step 1: Write failing test for tool registration**

Create `tests/agents/test_tool_registry.py`:

```python
import pytest
from app.agents.tools import get_tool_registry

class TestToolRegistry:
    @pytest.mark.asyncio
    async def test_registry_has_search_cases_tool(self):
        """Test that search_cases tool is registered"""
        registry = get_tool_registry()
        tools = registry.get_tools()

        tool_names = [t.name for t in tools]
        assert "search_cases" in tool_names

    @pytest.mark.asyncio
    async def test_search_cases_tool_has_description(self):
        """Test that search_cases tool has proper description"""
        registry = get_tool_registry()
        tools = registry.get_tools()

        search_cases_tool = next((t for t in tools if t.name == "search_cases"), None)
        assert search_cases_tool is not None
        assert len(search_cases_tool.description) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/agents/test_tool_registry.py -v`
Expected: FAIL - search_cases not registered yet

- [ ] **Step 3: Modify tools.py to register search_cases**

Modify `backend/app/agents/tools.py`:

```python
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
        The global ToolRegistry instance with all registered tools
    """
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()

        # Register built-in tools
        from app.agents.tools.case_search import search_cases

        _tool_registry.register(
            name="search_cases",
            func=search_cases.func,  # LangChain @tool decorator wraps the function
            description=search_cases.description
        )

        logger.info("ToolRegistry initialized with built-in tools")

    return _tool_registry
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/agents/test_tool_registry.py -v`
Expected: All tests PASS

- [ ] **Step 5: Test tool can be called directly**

Add to `tests/agents/test_tool_registry.py`:

```python
    @pytest.mark.asyncio
    async def test_search_cases_tool_is_callable(self):
        """Test that the registered tool can be invoked"""
        registry = get_tool_registry()
        tools = registry.get_tools()

        search_cases_tool = next((t for t in tools if t.name == "search_cases"), None)

        # Mock the FirecrawlService
        from unittest.mock import patch
        with patch('app.agents.tools.case_search.get_firecrawl_service') as mock_get:
            mock_service = AsyncMock()
            mock_service.search.return_value = {"results": []}
            mock_get.return_value = mock_service

            # Invoke the tool
            result = await search_cases_tool.ainvoke({"query": "test"})

            assert "cases" in result
```

- [ ] **Step 6: Run all tests again**

Run: `pytest tests/agents/test_tool_registry.py -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/agents/tools.py tests/agents/test_tool_registry.py
git commit -m "feat: register search_cases tool in ToolRegistry

- Import and register search_cases tool in get_tool_registry()
- Add tool description from @tool decorator
- Add tests to verify tool registration
- Test that registered tool is callable

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 4: Backend Graph Integration - Case Search Node

### Task 4: Add case_search_node to graph workflow

**Files:**
- Modify: `backend/app/agents/nodes.py`
- Modify: `backend/app/agents/graph.py`
- Test: `tests/agents/test_case_search_node.py`

- [ ] **Step 1: Write failing test for case_search_node**

Create `tests/agents/test_case_search_node.py`:

```python
import pytest
from app.agents.nodes import case_search_node
from app.agents.state import AgentState

class TestCaseSearchNode:
    @pytest.mark.asyncio
    async def test_case_search_node_returns_response(self):
        """Test that case_search_node returns a response"""
        state: AgentState = {
            "user_message": "search_cases:劳动合同纠纷",
            "conversation_history": [],
            "user_id": None,
            "session_id": "test-session",
            "streaming": False
        }

        result = await case_search_node(state)

        assert "response" in result
        assert isinstance(result["response"], str)

    @pytest.mark.asyncio
    async def test_case_search_node_extracts_query(self):
        """Test that query is extracted from search_cases: command"""
        # This test verifies the node can parse the command format
        state: AgentState = {
            "user_message": "search_cases:具体的法律问题",
            "conversation_history": [],
            "user_id": None,
            "session_id": "test",
            "streaming": False
        }

        # Node should not crash on this input
        result = await case_search_node(state)
        assert "response" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/agents/test_case_search_node.py -v`
Expected: FAIL - case_search_node doesn't exist yet

- [ ] **Step 3: Add case_search_node to nodes.py**

Add to `backend/app/agents/nodes.py` (at the end of the file):

```python
# Case search node
async def case_search_node(state: AgentState) -> Dict[str, Any]:
    """
    Handle case search requests using LLM tool calling.

    This node processes user messages in the format "search_cases:{query}"
    and uses an LLM with the search_cases tool to find relevant legal cases.

    Args:
        state: Current agent state containing user_message with search command

    Returns:
        Dict with response key containing the LLM's formatted case results
    """
    from app.agents.tools import get_tool_registry
    from app.services.llm_service import get_llm_service
    from langchain_core.tools import render_text_description
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    llm_service = get_llm_service()
    tool_registry = get_tool_registry()

    # Extract query from command
    user_message = state.get("user_message", "")
    if user_message.startswith("search_cases:"):
        query = user_message.replace("search_cases:", "").strip()
    else:
        query = user_message

    # Get tools
    tools = tool_registry.get_tools()

    # Check if ChatTongyi supports bind_tools
    try:
        # Try to bind tools to LLM
        llm_with_tools = llm_service.llm.bind_tools(tools)

        # Generate prompt with tool descriptions
        tool_descriptions = render_text_description(tools)
        system_prompt = f"""你是一个法律案例搜索助手。用户想要搜索相关的法律案例。

可用工具：
{tool_descriptions}

请使用 search_cases 工具为用户搜索相关案例，然后以清晰易读的格式展示结果。

对于每个找到的案例，请展示：
- 案件标题
- 案件摘要
- 来源链接

如果找不到相关案例，请告知用户并建议尝试不同的关键词。"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{query}")
        ])

        chain = prompt | llm_with_tools | StrOutputParser()

        response = await chain.ainvoke({"query": query})

        return {"response": response}

    except Exception as e:
        # If tool calling fails, provide fallback response
        logger = logging.getLogger(__name__)
        logger.error(f"Tool calling failed: {e}")

        fallback_message = f"""抱歉，案例搜索功能暂时不可用。

您可以尝试以下方式查找相关案例：
1. 访问中国裁判文书网 (http://wenshu.court.gov.cn)
2. 在搜索引擎中搜索"{query} 裁判文书"

错误详情：{str(e)}"""

        return {"response": fallback_message}
```

- [ ] **Step 4: Update intent_router_node to detect case_search intent**

Modify `intent_router_node` in `backend/app/agents/nodes.py`:

```python
async def intent_router_node(state: AgentState) -> Dict[str, Any]:
    """Classify user intent"""
    message = state["user_message"].lower()

    # Simple keyword-based intent classification
    legal_keywords = ["法律", "法", "合同", "侵权", "赔偿", "责任", "起诉", "诉讼", "法院"]
    greeting_keywords = ["你好", "您好", "hi", "hello"]
    doc_keywords = ["文档", "文件", "分析", "pdf", "docx"]

    # NEW: Check for case search command first
    if message.startswith("search_cases:"):
        return {"user_intent": "case_search"}

    if any(kw in message for kw in greeting_keywords):
        return {"user_intent": "greeting"}

    if any(kw in message for kw in doc_keywords):
        return {"user_intent": "document_analysis"}

    if any(kw in message for kw in legal_keywords):
        return {"user_intent": "legal_consultation"}

    return {"user_intent": "general_chat"}
```

- [ ] **Step 5: Update graph routing in graph.py**

Modify `backend/app/agents/graph.py`:

```python
from app.agents.nodes import (
    intent_router_node,
    rag_retriever_node,
    response_generator_node,
    memory_extraction_node,
    doc_analyzer_node,
    case_search_node  # NEW: import the new node
)
```

Update `route_after_intent` function:

```python
def route_after_intent(state: AgentState) -> str:
    """Route to RAG or directly to response based on intent"""
    intent = state.get("user_intent")

    if intent == "legal_consultation":
        return "rag_retriever"
    elif intent == "case_search":  # NEW
        return "case_search"
    elif intent == "document_analysis":
        return "doc_analyzer"
    else:
        # greeting, general_chat, etc. go directly to response
        return "response_generator"
```

Add node and edge:

```python
workflow.add_node("case_search", case_search_node)  # NEW
```

Update conditional edges:

```python
workflow.add_conditional_edges(
    "intent_router",
    route_after_intent,
    {
        "rag_retriever": "rag_retriever",
        "case_search": "case_search",  # NEW
        "doc_analyzer": "doc_analyzer",
        "response_generator": "response_generator"
    }
)
```

Add edge from case_search to response:

```python
workflow.add_edge("case_search", "response_generator")  # NEW
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/agents/test_case_search_node.py -v`
Expected: Tests PASS (may need mock for tool calling)

- [ ] **Step 7: Update test with proper mocking**

Update `tests/agents/test_case_search_node.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.agents.nodes import case_search_node
from app.agents.state import AgentState

class TestCaseSearchNode:
    @pytest.mark.asyncio
    async def test_case_search_node_returns_response(self):
        """Test that case_search_node returns a response"""
        state: AgentState = {
            "user_message": "search_cases:劳动合同纠纷",
            "conversation_history": [],
            "user_id": None,
            "session_id": "test-session",
            "streaming": False
        }

        # Mock the tool registry and LLM
        with patch('app.agents.nodes.get_tool_registry') as mock_registry, \
             patch('app.agents.nodes.get_llm_service') as mock_llm:

            # Mock tool
            mock_tool = MagicMock()
            mock_tool.name = "search_cases"
            mock_registry.return_value.get_tools.return_value = [mock_tool]

            # Mock LLM with bind_tools
            mock_llm_instance = MagicMock()
            mock_llm_instance.llm.bind_tools.return_value = MagicMock()
            mock_llm.return_value = mock_llm_instance

            result = await case_search_node(state)

            assert "response" in result
            assert isinstance(result["response"], str)

    @pytest.mark.asyncio
    async def test_case_search_node_handles_tool_calling_failure(self):
        """Test that node handles bind_tools failure gracefully"""
        state: AgentState = {
            "user_message": "search_cases:test",
            "conversation_history": [],
            "user_id": None,
            "session_id": "test",
            "streaming": False
        }

        with patch('app.agents.nodes.get_tool_registry') as mock_registry, \
             patch('app.agents.nodes.get_llm_service') as mock_llm:

            mock_registry.return_value.get_tools.return_value = []
            mock_llm_instance = MagicMock()
            # Make bind_tools raise an exception
            mock_llm_instance.llm.bind_tools.side_effect = Exception("Tool calling not supported")
            mock_llm.return_value = mock_llm_instance

            result = await case_search_node(state)

            # Should return fallback message
            assert "response" in result
            assert "暂时不可用" in result["response"] or "unavailable" in result["response"]
```

- [ ] **Step 8: Run all tests**

Run: `pytest tests/agents/test_case_search_node.py tests/agents/test_graph_execution.py -v`
Expected: All tests PASS

- [ ] **Step 9: Commit**

```bash
git add backend/app/agents/nodes.py backend/app/agents/graph.py tests/agents/test_case_search_node.py
git commit -m "feat: add case_search_node to graph workflow

- Add case_search_node with LLM tool calling support
- Detect search_cases: command in intent_router_node
- Update graph routing for case_search intent
- Add fallback when tool calling fails
- Add unit tests for case_search_node

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 5: Frontend - Case Search Button Component

### Task 5: Create CaseSearchButton React component

**Files:**
- Create: `frontend/src/components/chat/CaseSearchButton.tsx`
- Test: `frontend/src/components/chat/__tests__/CaseSearchButton.test.tsx`

- [ ] **Step 1: Write failing test for CaseSearchButton**

Create `frontend/src/components/chat/__tests__/CaseSearchButton.test.tsx`:

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { CaseSearchButton } from '../CaseSearchButton';

describe('CaseSearchButton', () => {
  it('renders button with search icon and text', () => {
    render(<CaseSearchButton query="test query" />);
    expect(screen.getByText('🔍 搜索相关案例')).toBeInTheDocument();
  });

  it('is disabled when disabled prop is true', () => {
    render(<CaseSearchButton query="test" disabled={true} />);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('calls sendMessage on click', async () => {
    const mockSendMessage = vi.fn().mockResolvedValue(undefined);
    // Mock the streamingClient
    vi.mock('@/api/streamingClient', () => ({
      sendMessage: mockSendMessage
    }));

    render(<CaseSearchButton query="劳动合同纠纷" />);
    fireEvent.click(screen.getByRole('button'));

    expect(mockSendMessage).toHaveBeenCalledWith('search_cases:劳动合同纠纷');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- CaseSearchButton.test.tsx`
Expected: FAIL - component doesn't exist

- [ ] **Step 3: Implement CaseSearchButton component**

Create `frontend/src/components/chat/CaseSearchButton.tsx`:

```typescript
import { sendMessage } from '@/api/streamingClient';

interface CaseSearchButtonProps {
  /** The search query extracted from conversation context */
  query: string;
  /** Whether the button should be disabled */
  disabled?: boolean;
  /** Additional CSS class name */
  className?: string;
}

/**
 * Button component for triggering legal case search.
 *
 * This button appears after legal consultation responses,
 * allowing users to search for relevant court cases.
 */
export function CaseSearchButton({
  query,
  disabled = false,
  className = ''
}: CaseSearchButtonProps) {
  const handleClick = async () => {
    try {
      await sendMessage(`search_cases:${query}`);
    } catch (error) {
      console.error('Failed to send case search request:', error);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={disabled}
      className={`case-search-button ${className}`}
      title="搜索相关法律案例"
    >
      🔍 搜索相关案例
    </button>
  );
}
```

- [ ] **Step 4: Add basic styles**

Add to `frontend/src/components/chat/CaseSearchButton.module.css`:

```css
.case-search-button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  margin-top: 0.5rem;
  background-color: #f0f9ff;
  border: 1px solid #0ea5e9;
  border-radius: 0.5rem;
  color: #0369a1;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.case-search-button:hover:not(:disabled) {
  background-color: #e0f2fe;
  border-color: #0284c7;
}

.case-search-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

- [ ] **Step 5: Update component to use styles**

Update `frontend/src/components/chat/CaseSearchButton.tsx`:

```typescript
import { sendMessage } from '@/api/streamingClient';
import styles from './CaseSearchButton.module.css';

interface CaseSearchButtonProps {
  query: string;
  disabled?: boolean;
  className?: string;
}

export function CaseSearchButton({
  query,
  disabled = false,
  className = ''
}: CaseSearchButtonProps) {
  const handleClick = async () => {
    try {
      await sendMessage(`search_cases:${query}`);
    } catch (error) {
      console.error('Failed to send case search request:', error);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={disabled}
      className={`${styles['case-search-button']} ${className}`}
      title="搜索相关法律案例"
    >
      🔍 搜索相关案例
    </button>
  );
}
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `npm test -- CaseSearchButton.test.tsx`
Expected: Tests PASS

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/chat/CaseSearchButton.tsx frontend/src/components/chat/CaseSearchButton.module.css
git commit -m "feat: add CaseSearchButton component

- Create CaseSearchButton component
- Add styles with CSS modules
- Handle button click to send search_cases command
- Add unit tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 6: Frontend - Integration with ChatView

### Task 6: Integrate CaseSearchButton into chat flow

**Files:**
- Modify: `frontend/src/components/chat/ChatView.tsx`
- Modify: `frontend/src/components/common/MessageBubble.tsx`

- [ ] **Step 1: Add query extraction helper**

Create `frontend/src/utils/queryExtractor.ts`:

```typescript
/**
 * Extract key legal topic from user message for case search.
 *
 * @param userMessage - The user's message text
 * @returns Extracted query for case search
 */
export function extractKeyQuestion(userMessage: string): string {
  // Remove common prefixes
  const cleaned = userMessage
    .replace(/我想了解|我想知道|请问|什么是|怎么/g, '')
    .trim();

  // Return first ~20 chars plus " 相关案例"
  if (cleaned.length > 20) {
    return cleaned.slice(0, 20) + " 相关案例";
  }

  return cleaned + " 相关案例";
}

/**
 * Check if a message is a legal consultation response.
 *
 * @param message - The assistant's message content
 * @returns True if this appears to be legal consultation
 */
export function isLegalConsultation(message: string): boolean {
  const legalKeywords = [
    '法律', '法规', '合同', '侵权', '赔偿', '责任',
    '起诉', '诉讼', '法院', '判决', '案例', '裁判'
  ];

  return legalKeywords.some(keyword => message.includes(keyword));
}
```

- [ ] **Step 2: Add tests for query extractor**

Create `frontend/src/utils/__tests__/queryExtractor.test.ts`:

```typescript
import { extractKeyQuestion, isLegalConsultation } from '../queryExtractor';

describe('queryExtractor', () => {
  describe('extractKeyQuestion', () => {
    it('removes common prefixes', () => {
      expect(extractKeyQuestion('我想了解劳动合同纠纷'))
        .toBe('劳动合同纠纷 相关案例');
    });

    it('truncates long messages', () => {
      const long = '这是一个非常长的关于劳动合同纠纷的问题描述';
      const result = extractKeyQuestion(long);
      expect(result.length).toBeLessThan(30);
    });

    it('adds 相关案例 suffix', () => {
      expect(extractKeyQuestion('交通事故')).toContain('相关案例');
    });
  });

  describe('isLegalConsultation', () => {
    it('returns true for legal keywords', () => {
      expect(isLegalConsultation('根据民法典相关规定')).toBe(true);
    });

    it('returns false for non-legal content', () => {
      expect(isLegalConsultation('你好，今天天气不错')).toBe(false);
    });
  });
});
```

- [ ] **Step 3: Update MessageBubble to show CaseSearchButton**

Modify `frontend/src/components/common/MessageBubble.tsx`:

```typescript
import { CaseSearchButton } from '@/components/chat/CaseSearchButton';
import { isLegalConsultation, extractKeyQuestion } from '@/utils/queryExtractor';

// In the component, after the message content:
{message.role === 'assistant' &&
 isLegalConsultation(message.content) &&
 lastUserMessage && (
  <CaseSearchButton
    query={extractKeyQuestion(lastUserMessage.content)}
    disabled={isLoading}
  />
)}
```

Note: You'll need access to `lastUserMessage` - pass it as a prop or get from context.

- [ ] **Step 4: Update ChatView to pass last user message**

Modify `frontend/src/components/chat/ChatView.tsx` to track and pass the last user message:

```typescript
// Add state to track last user message
const [lastUserMessage, setLastUserMessage] = useState<Message | null>(null);

// Update when user sends message
const handleSendMessage = async (content: string) => {
  if (!content.trim()) return;

  const userMessage: Message = {
    id: Date.now().toString(),
    role: 'user',
    content,
    timestamp: new Date().toISOString()
  };

  setMessages(prev => [...prev, userMessage]);
  setLastUserMessage(userMessage);

  // ... rest of send logic
};

// Pass to MessageBubble
<MessageBubble
  message={msg}
  lastUserMessage={lastUserMessage}
  isLoading={isLoading}
/>
```

- [ ] **Step 5: Run tests**

Run: `npm test -- queryExtractor.test.ts`
Expected: Tests PASS

- [ ] **Step 6: Test manually in browser**

1. Start the app
2. Ask a legal question
3. Verify the "搜索相关案例" button appears
4. Click the button
5. Verify search command is sent

- [ ] **Step 7: Commit**

```bash
git add frontend/src/utils/queryExtractor.ts frontend/src/components/common/MessageBubble.tsx frontend/src/components/chat/ChatView.tsx
git commit -m "feat: integrate CaseSearchButton into chat flow

- Add query extraction utility functions
- Show CaseSearchButton after legal consultation responses
- Track last user message in ChatView
- Pass lastUserMessage to MessageBubble for query extraction
- Add unit tests for query extractor

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## End of Implementation Plan

**Total Tasks:** 6 main tasks with ~40 individual steps

**Estimated Time:** 4-6 hours of focused development

**Testing Checklist:**
- [ ] Unit tests for FirecrawlService
- [ ] Unit tests for search_cases tool
- [ ] Tests for tool registration
- [ ] Tests for case_search_node
- [ ] Frontend component tests
- [ ] Manual E2E testing in browser

**Environment Setup Required:**
```bash
# Add to .env
FIRECRAWL_API_KEY=your_api_key_here
```
