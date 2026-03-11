from typing import Dict, Any, List, AsyncIterator, Optional
from app.agents.state import AgentState
from app.agents.utils import convert_to_langchain_messages
from app.services.document_service import get_document_service
from app.services.llm_service import get_llm_service
from app.services.memory_service import MemoryService
from app.services.memory_extraction_service import MemoryExtractionService
from app.services.session_service import SessionService
from app.database import get_db
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage
import logging
import json

logger = logging.getLogger(__name__)

# Default system prompt for legal consultation
DEFAULT_LEGAL_SYSTEM_PROMPT = """你是一个专业的法律咨询助手，为普通公众提供初步的法律信息参考。

重要原则：
1. 仅提供法律信息参考，不构成正式法律意见
2. 建议用户在重大事项上咨询专业律师
3. 基于提供的法律知识库回答，引用相关法规
4. 回答要清晰、易懂，避免过度专业术语

参考信息：
{context_str}

请基于以上参考信息回答用户的问题。如果参考信息不足，请说明这一点。"""

# System prompt builder
def build_system_prompt(context_str: str = "") -> str:
    """Build system prompt with optional RAG context."""
    if context_str:
        return DEFAULT_LEGAL_SYSTEM_PROMPT.format(context_str=context_str)
    return """你是一个友好的助手，为用户提供帮助。
回答要简洁、友好、有用。"""


async def intent_router_node(state: AgentState) -> Dict[str, Any]:
    """Classify user intent"""
    message = state["user_message"]

    # Check for case_search command first (before lowercasing)
    if message.startswith("search_cases:"):
        return {"user_intent": "case_search"}

    # Simple keyword-based intent classification
    message_lower = message.lower()
    legal_keywords = ["法律", "法", "合同", "侵权", "赔偿", "责任", "起诉", "诉讼", "法院"]
    greeting_keywords = ["你好", "您好", "hi", "hello"]
    doc_keywords = ["文档", "文件", "分析", "pdf", "docx"]  # NEW

    if any(kw in message_lower for kw in greeting_keywords):
        return {"user_intent": "greeting"}

    if any(kw in message_lower for kw in doc_keywords):  # NEW
        return {"user_intent": "document_analysis"}

    if any(kw in message_lower for kw in legal_keywords):
        return {"user_intent": "legal_consultation"}

    return {"user_intent": "general_chat"}


async def rag_retriever_node(state: AgentState) -> Dict[str, Any]:
    """Retrieve relevant context from knowledge base"""
    document_service = get_document_service()

    if state.get("user_intent") != "legal_consultation":
        return {"retrieved_context": [], "sources": []}

    try:
        # Determine category from message or use default
        category = None  # Could add category detection
        results = await document_service.search_knowledge(
            query=state["user_message"],
            category=category,
            n_results=5
        )

        # Format context for prompt
        context_str = _format_context_for_prompt(results)

        return {
            "retrieved_context": results,
            "context_str": context_str,
            "sources": [{"title": r.get("metadata", {}).get("title", ""), "score": r.get("score", 0)} for r in results]
        }
    except Exception as e:
        logger.error(f"Error in RAG retrieval: {e}")
        return {"retrieved_context": [], "context_str": "", "sources": []}


def _format_context_for_prompt(results: List[Dict[str, Any]]) -> str:
    """Format retrieved documents into context string"""
    if not results:
        return "未找到相关信息。"

    context_parts = []
    for i, result in enumerate(results[:5], 1):
        text = result.get("text", "")
        metadata = result.get("metadata", {})
        title = metadata.get("title", "未知来源")
        context_parts.append(f"[来源 {i}] {title}\n{text}")

    return "\n\n".join(context_parts)

# 短期记忆（Retrieve db） 长期记忆（Retrieve vector）用户爱好（Retrieve db）
async def _enhance_prompt_with_memory(
    base_prompt: str,
    user_id: str,
    user_message: str,
    db
) -> str:
    """
    Enhance system prompt with user memory (short-term, long-term, preferences).

    Args:
        base_prompt: Original system prompt
        user_id: User identifier
        user_message: Current user message for context
        db: Database session

    Returns:
        Enhanced prompt with memory context
    """
    try:
        # Initialize MemoryService
        memory_service = MemoryService(db)

        # Retrieve short-term context (last N sessions)
        short_term_context = await memory_service.get_short_term_context(
            user_id=user_id,
            limit=3
        )

        # Retrieve long-term memory (facts + summaries)
        long_term_memory = await memory_service.get_long_term_memory(
            user_id=user_id,
            query=user_message,
            top_k=5
        )

        # Retrieve user preferences
        preferences = await memory_service.get_preferences(user_id=user_id)

        # Build memory context string
        memory_context_parts = []

        # Add short-term context
        if short_term_context:
            context_summary = "短期对话历史（最近几次会话）：\n"
            for ctx in short_term_context:
                context_summary += f"- 会话: {ctx.get('title', 'N/A')}\n"
            memory_context_parts.append(context_summary)

        # Add long-term memory
        if long_term_memory:
            memory_summary = "长期记忆（相关信息）：\n"
            for mem in long_term_memory[:3]:  # Top 3 most relevant
                fact = mem.get("fact", "")
                if fact:
                    memory_summary += f"- {fact}\n"
            memory_context_parts.append(memory_summary)

        # Add user preferences
        if preferences:
            pref_summary = "用户偏好：\n"
            for key, value in preferences.items():
                pref_summary += f"- {key}: {value}\n"
            memory_context_parts.append(pref_summary)

        # Combine with base prompt
        if memory_context_parts:
            memory_section = "\n".join(memory_context_parts)
            enhanced_prompt = f"""{base_prompt}

用户记忆上下文：
{memory_section}

请利用以上记忆信息提供个性化回复。"""
        else:
            enhanced_prompt = base_prompt

        return enhanced_prompt

    except Exception as e:
        logger.error(f"Error enhancing prompt with memory: {e}")
        # Return base prompt on error (graceful degradation)
        return base_prompt


async def response_generator_node(state: AgentState) -> Dict[str, Any]:
    """Generate response using LangChain ChatTongyi with memory integration."""
    llm_service = get_llm_service()

    try:
        # Build base system prompt
        system_prompt = build_system_prompt(state.get("context_str", ""))

        # Enhance prompt with memory if user_id exists
        user_id: Optional[str] = state.get("user_id")
        if user_id:
            # Get database session
            db_gen = get_db()
            db = await db_gen.__anext__()

            try:
                system_prompt = await _enhance_prompt_with_memory(
                    base_prompt=system_prompt,
                    user_id=user_id,
                    user_message=state["user_message"],
                    db=db
                )
            except Exception as e:
                logger.error(f"Error retrieving user memory: {e}")
                # Continue with base prompt if memory retrieval fails
            finally:
                await db_gen.aclose()

        # Build LangChain prompt template
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{user_message}")
        ])

        # Build LCEL chain
        chain = prompt_template | llm_service.llm | StrOutputParser()

        # Convert conversation history
        history_messages = convert_to_langchain_messages(state["conversation_history"])

        # Invoke chain (non-streaming for graph execution)
        response = await chain.ainvoke({
            "history": history_messages,
            "user_message": state["user_message"]
        })

        return {"response": response, "error": ""}

    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return {
            "response": "抱歉，处理您的请求时出现错误。请稍后再试。",
            "error": str(e)
        }


async def response_generator_node_stream(state: AgentState) -> AsyncIterator[Dict[str, Any]]:
    """Generate streaming response using LangChain ChatTongyi with memory integration."""
    llm_service = get_llm_service()

    try:
        # Build base system prompt
        system_prompt = build_system_prompt(state.get("context_str", ""))

        # Enhance prompt with memory if user_id exists
        user_id: Optional[str] = state.get("user_id")
        if user_id:
            # Get database session
            db_gen = get_db()
            db = await db_gen.__anext__()

            try:
                system_prompt = await _enhance_prompt_with_memory(
                    base_prompt=system_prompt,
                    user_id=user_id,
                    user_message=state["user_message"],
                    db=db
                )
            except Exception as e:
                logger.error(f"Error retrieving user memory for streaming: {e}")
                # Continue with base prompt if memory retrieval fails
            finally:
                await db_gen.aclose()

        # Build LangChain prompt template
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{user_message}")
        ])

        # Build LCEL chain
        chain = prompt_template | llm_service.llm | StrOutputParser()

        # Convert conversation history
        history_messages = convert_to_langchain_messages(state["conversation_history"])

        # Yield start event
        yield {
            "event": "start",
            "data": {"intent": state.get("user_intent", "unknown")}
        }

        # Yield retrieved docs if any
        if state.get("sources"):
            yield {
                "event": "context",
                "data": {"sources": state["sources"]}
            }

        # Stream response using LangChain astream
        full_response = ""
        async for chunk in chain.astream({
            "history": history_messages,
            "user_message": state["user_message"]
        }):
            if chunk:
                full_response += chunk
                yield {
                    "event": "token",
                    "data": {"chunk": chunk, "full_response": full_response}
                }

        # Yield end event
        yield {
            "event": "end",
            "data": {"response": full_response}
        }

    except Exception as e:
        logger.error(f"Error generating streaming response: {e}")
        yield {
            "event": "error",
            "data": {"error": str(e)}
        }

# 记忆节点
async def memory_extraction_node(state: AgentState) -> Dict[str, Any]:
    """
    Extract and store long-term memories from conversation.

    This node is only executed for authenticated users (when user_id is present).
    It extracts user facts and generates conversation summaries.

    Args:
        state: Current agent state containing user_id, session_id, and conversation history

    Returns:
        Dict with memory extraction results
    """
    user_id = state.get("user_id")
    session_id = state.get("session_id")
    conversation_history = state.get("conversation_history", [])
    user_message = state.get("user_message", "")

    # Skip if not authenticated
    if not user_id:
        return {
            "memory_extracted": False,
            "facts_extracted": [],
            "summary_generated": None
        }

    try:
        # Get database session
        async for db in get_db():
            extraction_service = MemoryExtractionService(db)
            session_service = SessionService(db)

            # Get message count
            session = await session_service.get_session(session_id)
            message_count = session.message_count if session else 0

            # Build last N messages for context
            last_n_messages = (conversation_history[-5:] if conversation_history else []) + [{"role": "user", "content": user_message}]

            # Extract memories
            results = await extraction_service.process_conversation_memory(
                user_id=user_id,
                session_id=session_id,
                message_count=message_count,
                last_user_message=user_message,
                last_n_messages=last_n_messages
            )

            return {
                "memory_extracted": True,
                "facts_extracted": results.get("facts_extracted", []),
                "summary_generated": results.get("summary_generated")
            }
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error in memory_extraction_node: {e}")
        return {
            "memory_extracted": False,
            "facts_extracted": [],
            "summary_generated": None
        }

# 文档node节点
async def doc_analyzer_node(state: AgentState) -> Dict[str, Any]:
    """
    Document analysis node (placeholder for future implementation).

    This is a demonstration of how easy it is to add new agents to the system.
    In a real implementation, this would:
    - Extract document content from the user message
    - Analyze the document using appropriate tools
    - Return structured analysis results

    Args:
        state: Current agent state

    Returns:
        Dict with document analysis results
    """
    user_message = state.get("user_message", "")

    # Placeholder: In real implementation, this would:
    # 1. Parse document from message or attachment
    # 2. Use document analysis tools
    # 3. Return structured analysis

    return {
        "doc_analysis": f"文档分析请求: {user_message}",
        "context_str": "文档分析功能即将推出。当前为演示模式。",
        "sources": [{"type": "document", "message": "示例文档源"}]
    }


async def case_search_node(state: AgentState) -> Dict[str, Any]:
    """
    Handle case search requests using LLM tool calling.

    This node uses an LLM with tools to process case search requests.
    The query is extracted from the "search_cases:" command prefix.

    Args:
        state: Current agent state containing user_message with search_cases: prefix

    Returns:
        Dict with response containing formatted case search results
    """
    from app.agents.tools import get_tool_registry
    from langchain_core.tools import render_text_description

    llm_service = get_llm_service()
    tool_registry = get_tool_registry()

    # Extract query from command
    query = state["user_message"].replace("search_cases:", "").strip()

    # Get the search_cases tool
    search_cases_tool = tool_registry.get_tool("search_cases")

    if not search_cases_tool:
        logger.error("search_cases tool not found in registry")
        return {
            "response": "抱歉，案例搜索功能暂时不可用。",
            "error": "search_cases tool not registered"
        }

    # Bind tools to LLM
    llm_with_tools = llm_service.llm.bind_tools([search_cases_tool])

    # Generate prompt with tool descriptions
    tool_descriptions = render_text_description([search_cases_tool])
    system_prompt = f"""你是一个法律案例搜索助手。用户想要搜索相关的法律案例。

可用工具：
{tool_descriptions}

请使用 search_cases 工具为用户搜索相关案例，然后以清晰易读的格式展示结果。每个案例应包含：
- 案例标题
- 案例摘要
- 来源链接
- 相关性评分"""

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{query}")
    ])

    # Build and invoke chain
    chain = prompt_template | llm_with_tools | StrOutputParser()

    try:
        response = await chain.ainvoke({"query": query})
        return {"response": response, "error": ""}
    except Exception as e:
        logger.error(f"Error in case_search_node: {e}")
        return {
            "response": "抱歉，案例搜索时出现错误。请稍后再试。",
            "error": str(e)
        }
