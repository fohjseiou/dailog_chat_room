from typing import List, Dict, Any, AsyncIterator, Optional
import dashscope
from dashscope import Generation
from app.config import get_settings
import logging
import asyncio

logger = logging.getLogger(__name__)


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
            # Default legal consultation system prompt
            default_system_prompt = """你是一个专业的法律咨询助手，为普通公众提供初步的法律信息参考。

重要原则：
1. 仅提供法律信息参考，不构成正式法律意见
2. 建议用户在重大事项上咨询专业律师
3. 回答要清晰、易懂，避免过度专业术语
4. 如果不确定，请说明需要更多信息"""

            # Build messages for Qwen API (Qwen uses list format)
            messages = []

            # Add system prompt
            messages.append({
                "role": "system",
                "content": system_prompt or default_system_prompt
            })

            # Add conversation history (last 10 messages)
            for msg in conversation_history[-10:]:
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
                    temperature=0.7,
                    top_p=0.9,
                    max_tokens=2000
                )
            )

            if response.status_code != 200:
                logger.error(f"DashScope API error: {response.code} - {response.message}")
                return "抱歉，我现在无法回答。请稍后再试。如果您有紧急的法律问题，建议咨询专业律师。"

            assistant_message = response.output.choices[0].message.content
            logger.info(f"Qwen response generated, tokens used: {response.usage.total_tokens}")
            return assistant_message

        except Exception as e:
            logger.error(f"Error generating Qwen response: {e}")
            # Return a fallback error message
            return "抱歉，我现在无法回答。请稍后再试。如果您有紧急的法律问题，建议咨询专业律师。"

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
            default_system_prompt = """你是一个专业的法律咨询助手，为普通公众提供初步的法律信息参考。

重要原则：
1. 仅提供法律信息参考，不构成正式法律意见
2. 建议用户在重大事项上咨询专业律师
3. 回答要清晰、易懂，避免过度专业术语
4. 如果不确定，请说明需要更多信息"""

            messages = []

            messages.append({
                "role": "system",
                "content": system_prompt or default_system_prompt
            })

            for msg in conversation_history[-10:]:
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
                    temperature=0.7,
                    top_p=0.9,
                    stream=True,
                    result_format='message',
                    max_tokens=2000
                )

            stream_gen = await loop.run_in_executor(None, get_stream_generator)

            # Yield chunks from the stream
            for response in stream_gen:
                if response.status_code == 200 and response.output:
                    for choice in response.output.choices:
                        if choice.message and choice.message.content:
                            yield choice.message.content

        except Exception as e:
            logger.error(f"Error in streaming Qwen response: {e}")
            yield "抱歉，我现在无法回答。请稍后再试。"


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the LLM service singleton"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
