# Legal Case Search Feature Design

**Date:** 2025-03-11
**Status:** Design Approved

## Goal

Add a legal case search capability that allows users to find relevant court cases after receiving legal consultation responses.

## Architecture

```
User asks legal question → System responds (RAG-based)
                         ↓
                 [Search Related Cases] button
                         ↓
   Frontend sends: "search_cases:{extracted_query}"
                         ↓
     intent_router detects "case_search" intent
                         ↓
              LLM calls search_cases_tool
                         ↓
      Tool uses Firecrawl API to search web
                         ↓
   LLM generates structured response (with case list)
                         ↓
            Display results directly in chat
```

## Components

### 1. Backend Tool Implementation

**File:** `backend/app/agents/tools/case_search.py` (new file)

**Directory Structure:**
```
backend/app/agents/
├── tools.py              # Existing: ToolRegistry
├── tools/                # NEW: Tool implementations directory
│   ├── __init__.py
│   └── case_search.py    # NEW: Case search tool implementation
```

**Tool Implementation:**
```python
from langchain_core.tools import tool
import logging

logger = logging.getLogger(__name__)

@tool
async def search_cases(query: str, limit: int = 5) -> dict:
    """
    Search for relevant legal cases and court decisions on the web.

    Args:
        query: Search query for finding relevant cases
        limit: Maximum number of cases to return (default: 5)

    Returns:
        Dictionary with case list and metadata
    """
    try:
        # Use Firecrawl MCP for web search
        from app.services.firecrawl_service import get_firecrawl_service

        firecrawl = get_firecrawl_service()

        # Build search query focused on legal cases
        search_query = f"{query} 裁判文书 案例 判决"

        # Perform search
        results = await firecrawl.search(
            query=search_query,
            limit=limit,
            scrape_options={"formats": ["markdown"]}
        )

        # Format results
        cases = []
        for result in results.get("results", [])[:limit]:
            cases.append({
                "title": result.get("title", "Unknown"),
                "summary": result.get("markdown", "")[:500],
                "url": result.get("url", ""),
                "relevance": result.get("score", 0)
            })

        return {
            "cases": cases,
            "total_found": len(cases)
        }

    except Exception as e:
        logger.error(f"Case search failed: {e}")
        return {
            "cases": [],
            "total_found": 0,
            "error": str(e)
        }
```

### 2. Firecrawl Service

**File:** `backend/app/services/firecrawl_service.py` (new file)

**Responsibilities:**
- Wrap Firecrawl API calls
- Handle API key configuration
- Provide search and scrape methods

**Implementation:**
```python
from app.config import get_settings
from mcp__firecrawl import firecrawl_search
import logging

logger = logging.getLogger(__name__)

class FirecrawlService:
    """Service for Firecrawl API integration"""

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.firecrawl_api_key

    async def search(
        self,
        query: str,
        limit: int = 5,
        scrape_options: dict = None
    ) -> dict:
        """
        Perform web search using Firecrawl

        Args:
            query: Search query
            limit: Max results
            scrape_options: Options for content extraction

        Returns:
            Search results dictionary
        """
        try:
            # Use Firecrawl MCP tool
            results = await firecrawl_search(
                query=f"{query} site:中国裁判文书网 OR site:法院案例",
                limit=limit,
                scrape_options=scrape_options or {}
            )

            return results

        except Exception as e:
            logger.error(f"Firecrawl search error: {e}")
            raise
```

### 3. Tool Registration

**File:** `backend/app/agents/tools.py` (modify existing)

**Changes:**
```python
# Import tool implementation
from app.agents.tools.case_search import search_cases

def get_tool_registry() -> ToolRegistry:
    """Get or create the global ToolRegistry singleton"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
        # Register built-in tools
        _tool_registry.register(
            name="search_cases",
            func=search_cases,
            description="Search for relevant legal cases and court decisions"
        )
    return _tool_registry
```

### 4. Graph Integration

**File:** `backend/app/agents/nodes.py` (modify existing)

**Changes to `intent_router_node`:**
```python
async def intent_router_node(state: AgentState) -> Dict[str, Any]:
    """Classify user intent"""
    message = state["user_message"].lower()

    # Existing keywords
    legal_keywords = ["法律", "法", "合同", "侵权", "赔偿", "责任", "起诉", "诉讼", "法院"]
    greeting_keywords = ["你好", "您好", "hi", "hello"]
    doc_keywords = ["文档", "文件", "分析", "pdf", "docx"]

    # NEW: Check for case search command
    if message.startswith("search_cases:"):
        return {"user_intent": "case_search"}

    # ... existing logic ...
```

**New Node for Tool Calling:**
```python
async def case_search_node(state: AgentState) -> Dict[str, Any]:
    """
    Handle case search requests using LLM tool calling.

    This node uses an LLM with tools to process case search requests.
    """
    from app.agents.tools import get_tool_registry
    from app.services.llm_service import get_llm_service
    from langchain_core.tools import render_text_description

    llm_service = get_llm_service()
    tool_registry = get_tool_registry()

    # Extract query from command
    query = state["user_message"].replace("search_cases:", "").strip()

    # Get tools
    tools = tool_registry.get_tools()

    # Bind tools to LLM (ChatTongyi supports tool calling)
    llm_with_tools = llm_service.llm.bind_tools(tools)

    # Generate prompt with tool descriptions
    tool_descriptions = render_text_description(tools)
    system_prompt = f"""你是一个法律案例搜索助手。用户想要搜索相关的法律案例。

可用工具：
{tool_descriptions}

请使用 search_cases 工具为用户搜索相关案例，然后以清晰易读的格式展示结果。"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{query}")
    ])

    chain = prompt | llm_with_tools | StrOutputParser()

    response = await chain.ainvoke({"query": query})

    return {"response": response}
```

**Graph Routing Update (in `graph.py`):**
```python
def route_after_intent(state: AgentState) -> str:
    """Route to appropriate handler based on intent"""
    intent = state.get("user_intent")

    if intent == "legal_consultation":
        return "rag_retriever"
    elif intent == "case_search":  # NEW
        return "case_search"
    elif intent == "document_analysis":
        return "doc_analyzer"
    else:
        return "response_generator"

# Add node
workflow.add_node("case_search", case_search_node)

# Add routing
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

# Connect case_search to response
workflow.add_edge("case_search", "response_generator")
```

### 5. Frontend Component

**File:** `frontend/src/components/chat/CaseSearchButton.tsx` (new file)

**Implementation:**
```typescript
import { sendMessage } from '@/api/streamingClient';

interface CaseSearchButtonProps {
  query: string;           // Extracted from conversation context
  disabled?: boolean;
}

export function CaseSearchButton({ query, disabled }: CaseSearchButtonProps) {
  const handleSearch = async () => {
    // Send search command as user message
    await sendMessage(`search_cases:${query}`);
  };

  return (
    <button
      onClick={handleSearch}
      disabled={disabled}
      className="case-search-button"
    >
      🔍 搜索相关案例
    </button>
  );
}
```

**Integration in MessageBubble:**
```typescript
// In MessageBubble.tsx
{message.role === 'assistant' && isLegalConsultation() && (
  <CaseSearchButton
    query={extractKeyQuestion(lastUserMessage)}
    disabled={isLoading}
  />
)}
```

### 6. Query Extraction Logic

**Helper Function:**
```typescript
// Extract key legal topic from user message for case search
function extractKeyQuestion(userMessage: string): string {
  // Simple extraction: get first sentence or key phrase
  // Could be enhanced with NLP later

  // Remove common prefixes
  const cleaned = userMessage
    .replace(/我想了解|我想知道|请问|什么是/g, '')
    .trim();

  // Return first ~20 chars as search query
  return cleaned.slice(0, 20) + " 相关案例";
}
```

## Configuration

**Environment Variables:**
```bash
# Add to .env
FIRECRAWL_API_KEY=your_api_key_here
```

**Config Update (`app/config.py`):**
```python
class Settings(BaseSettings):
    # ... existing ...
    firecrawl_api_key: str = Field(default="", env="FIRECRAWL_API_KEY")
```

## Data Flow

1. User receives legal consultation response (intent: `legal_consultation`)
2. Frontend displays "Search Related Cases" button (based on intent)
3. User clicks button
4. Frontend extracts query from conversation context
5. Frontend sends `search_cases:{query}` message
6. `intent_router` detects `case_search` intent
7. Graph routes to `case_search_node`
8. LLM with tools invokes `search_cases` tool
9. Tool uses Firecrawl API to search web
10. LLM formats response with case list
11. Response displayed in chat as assistant message

## Error Handling

**Comprehensive Error Scenarios:**

| Error | Handler | User Message |
|-------|---------|--------------|
| Firecrawl API key missing | Config validation | "Case search not configured" |
| Firecrawl unavailable | Catch exception | "Case search temporarily unavailable" |
| No cases found | Check empty results | "No relevant cases found. Try different keywords" |
| Timeout | Set 30s limit | "Search took too long. Please try again." |
| Rate limit exceeded | Handle 429 | "Too many searches. Please wait a moment." |
| Invalid query | Validate input | "Search query is too short. Provide more details." |
| Malformed response | Parse safely | "Received invalid data. Please try again." |

**Error Recovery:**
- Log all errors for monitoring
- Return user-friendly messages
- Allow retry without refreshing

## State Management

**Case search results are:**
- Transient: Displayed in chat, not persisted to database
- Part of conversation history: Saved as messages (like other chat content)
- Not stored separately: No new database tables needed

**Rationale:** Case search results are part of the conversation flow, similar to RAG context. They should be preserved in message history for context but don't need separate persistence.

## Testing

### Unit Tests

**File:** `tests/agents/tools/test_case_search.py`

```python
import pytest
from app.agents.tools.case_search import search_cases

class TestCaseSearchTool:
    @pytest.mark.asyncio
    async def test_search_cases_with_valid_query(self):
        result = await search_cases("劳动合同纠纷")
        assert "cases" in result
        assert isinstance(result["cases"], list)

    @pytest.mark.asyncio
    async def test_search_cases_with_limit(self):
        result = await search_cases("交通事故", limit=3)
        assert len(result["cases"]) <= 3

    @pytest.mark.asyncio
    async def test_search_cases_handles_errors(self):
        # Mock Firecrawl error
        result = await search_cases("")  # Empty query
        assert "error" in result or result["cases"] == []
```

### Integration Tests

**File:** `tests/agents/test_graph_case_search.py`

```python
import pytest
from app.agents.graph import get_unified_agent_graph

class TestCaseSearchIntegration:
    @pytest.mark.asyncio
    async def test_case_search_intent_routing(self):
        state = {
            "user_message": "search_cases:劳动合同纠纷",
            "conversation_history": [],
            "user_id": None,
            "session_id": "test-session",
            "streaming": False
        }

        graph = get_unified_agent_graph()
        result = await graph.ainvoke(state)

        assert "response" in result
        assert "案例" in result["response"] or "cases" in result["response"]
```

### E2E Tests

**File:** `tests/e2e/test_case_search_flow.py`

```python
class TestCaseSearchE2E:
    async def test_user_clicks_search_button(self, test_client):
        # 1. Send legal question
        # 2. Verify search button appears
        # 3. Click search button
        # 4. Verify results displayed
        pass
```

### Test Data

**Mock Case Search Results:**
```python
MOCK_CASE_RESULTS = {
    "cases": [
        {
            "title": "张三诉公司劳动合同纠纷案",
            "summary": "法院判决公司支付违法解除赔偿金...",
            "court": "北京市朝阳区人民法院",
            "date": "2024-01-15",
            "url": "https://example.com/case/123"
        }
    ],
    "total_found": 1
}
```

## Implementation Order

### Phase 1: Backend Infrastructure
1. Create `backend/app/agents/tools/` directory
2. Implement `FirecrawlService` (with mock for testing)
3. Implement `search_cases` tool
4. Register tool in `ToolRegistry`
5. Create `case_search_node` with LLM tool calling
6. Update graph routing

### Phase 2: Frontend Integration
7. Implement `CaseSearchButton` component
8. Add query extraction helper
9. Integrate button in `MessageBubble`
10. Handle search responses in chat stream

### Phase 3: Testing & Polish
11. Write unit tests
12. Write integration tests
13. Add error handling
14. Add loading states
15. Test full flow

## Open Questions

1. **LLM Tool Calling Support:** Does ChatTongyi API support function calling? Need to verify with `tongyi` Python SDK documentation.

2. **Search Source Priority:** Should we prioritize specific legal databases (中国裁判文书网) or general web search?

3. **Result Caching:** Should we cache case search results by query to avoid duplicate API calls?

4. **Query Enhancement:** Should LLM rewrite user queries for better search results?

## Dependencies

- **Firecrawl MCP:** Already available via MCP tools
- **ChatTongyi Tool Calling:** Need to verify SDK support
- **LangChain Tool Binding:** Supported in current version
