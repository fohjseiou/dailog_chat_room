"""LLM service using LangChain ChatTongyi for Qwen integration."""

from typing import List, Dict, Any, AsyncIterator, Optional
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage
from app.config import get_settings
from app.agents.utils import convert_to_langchain_messages
import logging

logger = logging.getLogger(__name__)

# Constants
DEFAULT_SYSTEM_PROMPT = """你是一个专业的法律咨询助手，为普通公众提供初步的法律信息参考。

重要原则：
1. 仅提供法律信息参考，不构成正式法律意见
2. 建议用户在重大事项上咨询专业律师
3. 回答要清晰、易懂，避免过度专业术语
4. 如果不确定，请说明需要更多信息"""

MAX_HISTORY_MESSAGES = 10
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.9
MAX_TOKENS = 2000
FALLBACK_ERROR_MESSAGE = "抱歉，我现在无法回答。请稍后再试。如果您有紧急的法律问题，建议咨询专业律师。"


class LLMService:
    """Service for interacting with Qwen LLM via LangChain ChatTongyi."""

    def __init__(self):
        settings = get_settings()
        # Use LangChain ChatTongyi instead of DashScope SDK
        self.llm = ChatTongyi(
            model=settings.dashscope_model,
            dashscope_api_key=settings.dashscope_api_key,
            temperature=DEFAULT_TEMPERATURE,
            top_p=DEFAULT_TOP_P,
            max_tokens=MAX_TOKENS,
        )

    def _build_prompt_template(self, system_prompt: Optional[str] = None) -> ChatPromptTemplate:
        """Build LangChain prompt template."""
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt or DEFAULT_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{user_message}")
        ])

    async def generate_response(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a response using LangChain ChatTongyi.

        Args:
            message: The user's current message
            conversation_history: List of previous messages
            system_prompt: Optional system prompt to override default

        Returns:
            The LLM's response as a string
        """
        try:
            # Build prompt template
            prompt = self._build_prompt_template(system_prompt)

            # Build LCEL chain
            chain = prompt | self.llm | StrOutputParser()

            # Convert history to LangChain format
            history_messages = convert_to_langchain_messages(
                conversation_history[-MAX_HISTORY_MESSAGES:]
            )

            # Invoke chain
            response = await chain.ainvoke({
                "history": history_messages,
                "user_message": message
            })

            logger.info("ChatTongyi response generated successfully")
            return response

        except Exception as e:
            logger.error(f"Error generating ChatTongyi response: {e}")
            return FALLBACK_ERROR_MESSAGE

    async def generate_response_stream(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response using LangChain ChatTongyi.

        Args:
            message: The user's current message
            conversation_history: List of previous messages
            system_prompt: Optional system prompt to override default

        Yields:
            Chunks of the response as they arrive
        """
        try:
            # Build prompt template
            prompt = self._build_prompt_template(system_prompt)

            # Build LCEL chain
            chain = prompt | self.llm | StrOutputParser()

            # Convert history to LangChain format
            history_messages = convert_to_langchain_messages(
                conversation_history[-MAX_HISTORY_MESSAGES:]
            )

            # Stream response using LangChain astream
            async for chunk in chain.astream({
                "history": history_messages,
                "user_message": message
            }):
                if chunk:
                    yield chunk

        except Exception as e:
            logger.error(f"Error in streaming ChatTongyi response: {e}")
            yield FALLBACK_ERROR_MESSAGE


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
