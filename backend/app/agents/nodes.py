from typing import Dict, Any, List, AsyncIterator
from app.agents.state import AgentState
from app.agents.utils import convert_to_langchain_messages
from app.services.document_service import get_document_service
from app.services.llm_service import get_llm_service
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


async def response_generator_node(state: AgentState) -> Dict[str, Any]:
    """Generate response using LangChain ChatTongyi."""
    llm_service = get_llm_service()

    try:
        # Build system prompt
        system_prompt = build_system_prompt(state.get("context_str", ""))

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
    """Generate streaming response using LangChain ChatTongyi."""
    llm_service = get_llm_service()

    try:
        # Build system prompt
        system_prompt = build_system_prompt(state.get("context_str", ""))

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
