from typing import Dict, Any, List, AsyncIterator, Optional
from app.agents.state import AgentState
from app.agents.utils import convert_to_langchain_messages
from app.services.document_service import get_document_service
from app.services.llm_service import get_llm_service
from app.services.memory_service import MemoryService
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
    message = state["user_message"].lower()

    # Simple keyword-based intent classification
    legal_keywords = ["法律", "法", "合同", "侵权", "赔偿", "责任", "起诉", "诉讼", "法院"]
    greeting_keywords = ["你好", "您好", "hi", "hello"]

    if any(kw in message for kw in greeting_keywords):
        return {"user_intent": "greeting"}

    if any(kw in message for kw in legal_keywords):
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

        # Invoke chain
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
