from typing import List, Dict, Any, AsyncIterator, Optional
import dashscope
from dashscope import Generation
from app.config import get_settings
import logging
import asyncio

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
    """Service for interacting with DashScope Qwen LLM"""

    def __init__(self):
        settings = get_settings()
        dashscope.api_key = settings.dashscope_api_key
        self.model = settings.dashscope_model

    async def generate_response(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a response from Qwen LLM

        Args:
            message: The user's current message
            conversation_history: List of previous messages
            system_prompt: Optional system prompt to override default

        Returns:
            The LLM's response as a string
        """
        try:
            # Build messages for Qwen API (Qwen uses list format)
            messages = []

            # Add system prompt
            messages.append({
                "role": "system",
                "content": system_prompt or DEFAULT_SYSTEM_PROMPT
            })

            # Add conversation history (last N messages)
            for msg in conversation_history[-MAX_HISTORY_MESSAGES:]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            # Add current message
            messages.append({
                "role": "user",
                "content": message
            })

            # Call DashScope Qwen API (run in thread pool since it's sync)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: Generation.call(
                    model=self.model,
                    messages=messages,
                    result_format='message',
                    temperature=DEFAULT_TEMPERATURE,
                    top_p=DEFAULT_TOP_P,
                    max_tokens=MAX_TOKENS
                )
            )

            if response.status_code != 200:
                logger.error(f"DashScope API error: {response.code} - {response.message}")
                return FALLBACK_ERROR_MESSAGE

            assistant_message = response.output.choices[0].message.content
            logger.info(f"Qwen response generated, tokens used: {response.usage.total_tokens}")
            return assistant_message

        except Exception as e:
            logger.error(f"Error generating Qwen response: {e}")
            # Return a fallback error message
            return FALLBACK_ERROR_MESSAGE

    async def generate_response_stream(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response from Qwen

        Args:
            message: The user's current message
            conversation_history: List of previous messages
            system_prompt: Optional system prompt to override default

        Yields:
            Chunks of the response as they arrive
        """
        try:
            messages = []

            messages.append({
                "role": "system",
                "content": system_prompt or DEFAULT_SYSTEM_PROMPT
            })

            for msg in conversation_history[-MAX_HISTORY_MESSAGES:]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            messages.append({
                "role": "user",
                "content": message
            })

            # Stream the response from Qwen (run in thread pool)
            loop = asyncio.get_event_loop()

            # Get the generator
            def get_stream_generator():
                return Generation.call(
                    model=self.model,
                    messages=messages,
                    temperature=DEFAULT_TEMPERATURE,
                    top_p=DEFAULT_TOP_P,
                    stream=True,
                    result_format='message',
                    max_tokens=MAX_TOKENS
                )

            stream_gen = await loop.run_in_executor(None, get_stream_generator)

            # Yield chunks from the stream (DashScope returns the full content in each iteration if using result_format='message')
            last_content = ""
            for response in stream_gen:
                if response.status_code == 200 and response.output:
                    for choice in response.output.choices:
                        if choice.message and choice.message.content:
                            full_content = choice.message.content
                            # Calculate delta
                            delta = full_content[len(last_content):]
                            if delta:
                                last_content = full_content
                                yield delta

        except Exception as e:
            logger.error(f"Error in streaming Qwen response: {e}")
            yield FALLBACK_ERROR_MESSAGE


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the LLM service singleton"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
