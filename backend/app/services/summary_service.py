from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.models.session import Session as SessionModel
from app.models.message import Message
from app.services.llm_service import get_llm_service
from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Summary generation prompt
SUMMARY_SYSTEM_PROMPT = """你是一个专业的对话摘要助手。请将用户和法律咨询助手之间的对话总结为简洁的摘要。

摘要要求：
1. 突出用户的主要问题和需求
2. 总结提供的法律信息要点
3. 简洁明了，通常在2-4句话
4. 使用中文输出
5. 不要包含无关的寒暄内容

请直接输出摘要，不要添加"摘要："等前缀。"""


class SummaryService:
    """Service for generating and managing session summaries"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm_service = get_llm_service()

    async def should_generate_summary(self, session_id: str) -> bool:
        """
        Check if a session should have a summary generated

        Returns True if:
        - Message count >= threshold, OR
        - Total tokens >= threshold
        - No summary exists yet
        """
        # Get session
        result = await self.db.execute(
            select(SessionModel).where(SessionModel.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            return False

        # Already has summary
        if session.summary:
            return False

        # Check message count threshold
        if session.message_count >= settings.summary_message_threshold:
            return True

        # Check token threshold (estimate: 1 token ≈ 1.5 Chinese chars)
        # For simplicity, we'll just check if message count is high enough
        return session.message_count >= max(5, settings.summary_message_threshold // 2)

    async def generate_summary(self, session_id: str) -> str:
        """
        Generate a summary for a session

        Args:
            session_id: Session ID

        Returns:
            Generated summary text
        """
        # Get session with messages
        result = await self.db.execute(
            select(SessionModel)
            .where(SessionModel.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Get conversation history
        from app.services.message_service import MessageService
        message_service = MessageService(self.db)
        messages = await message_service.get_messages_by_session(session_id)

        if not messages:
            return "空对话"

        # Build conversation text for summary
        conversation_parts = []
        for msg in messages:
            role = "用户" if msg.role == "user" else "助手"
            conversation_parts.append(f"{role}：{msg.content}")

        conversation_text = "\n".join(conversation_parts)

        # Truncate if too long (keep recent messages)
        max_chars = 4000
        if len(conversation_text) > max_chars:
            # Keep recent messages
            conversation_text = conversation_text[-max_chars:]

        # Generate summary using LLM
        summary_prompt = f"""请将以下对话总结为简洁的摘要：

{conversation_text}

摘要："""

        try:
            summary = await self.llm_service.generate_response(
                message=summary_prompt,
                conversation_history=[],
                system_prompt=SUMMARY_SYSTEM_PROMPT
            )

            # Clean up the summary (remove common prefixes)
            summary = summary.strip()
            for prefix in ["摘要：", "摘要:", "Summary:", "摘要：", "【摘要】", "摘要: "]:
                if summary.startswith(prefix):
                    summary = summary[len(prefix):].strip()
                    break

            # Save to database
            session.summary = summary
            await self.db.commit()
            await self.db.refresh(session)

            logger.info(f"Generated summary for session {session_id}: {summary[:50]}...")
            return summary

        except Exception as e:
            logger.error(f"Error generating summary for session {session_id}: {e}")
            # Return a fallback summary
            fallback_summary = self._generate_fallback_summary(messages)
            session.summary = fallback_summary
            await self.db.commit()
            return fallback_summary

    def _generate_fallback_summary(self, messages: List[Message]) -> str:
        """Generate a simple fallback summary without LLM"""
        # Get first user message
        first_user_msg = None
        last_assistant_msg = None

        for msg in messages:
            if msg.role == "user" and first_user_msg is None:
                first_user_msg = msg.content
            elif msg.role == "assistant":
                last_assistant_msg = msg.content

        if first_user_msg and last_assistant_msg:
            # Truncate messages
            first = first_user_msg[:100] + "..." if len(first_user_msg) > 100 else first_user_msg
            return f"用户咨询：{first}"
        elif first_user_msg:
            first = first_user_msg[:100] + "..." if len(first_user_msg) > 100 else first_user_msg
            return f"用户咨询：{first}"
        else:
            return f"对话包含 {len(messages)} 条消息"

    async def get_summary(self, session_id: str) -> Optional[str]:
        """
        Get the summary for a session, generating if needed

        Args:
            session_id: Session ID

        Returns:
            Summary text or None if session not found
        """
        result = await self.db.execute(
            select(SessionModel).where(SessionModel.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            return None

        if session.summary:
            return session.summary

        # Generate summary if it doesn't exist
        if await self.should_generate_summary(session_id):
            return await self.generate_summary(session_id)

        return None

    async def regenerate_summary(self, session_id: str) -> str:
        """
        Force regenerate a summary for a session

        Args:
            session_id: Session ID

        Returns:
            Generated summary text
        """
        # Clear existing summary
        result = await self.db.execute(
            select(SessionModel).where(SessionModel.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.summary = None
        await self.db.commit()

        # Generate new summary
        return await self.generate_summary(session_id)

    async def generate_summaries_for_sessions(
        self,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Generate summaries for sessions that need them

        Args:
            limit: Maximum number of sessions to process

        Returns:
            Dict with processed, skipped, and failed counts
        """
        # Get sessions without summaries that have enough messages
        result = await self.db.execute(
            select(SessionModel)
            .where(
                (SessionModel.summary.is_(None)) &
                (SessionModel.message_count >= settings.summary_message_threshold // 2)
            )
            .order_by(SessionModel.updated_at.desc())
            .limit(limit)
        )
        sessions = result.scalars().all()

        processed = 0
        skipped = 0
        failed = 0

        for session in sessions:
            try:
                await self.generate_summary(session.id)
                processed += 1
            except Exception as e:
                logger.error(f"Failed to generate summary for session {session.id}: {e}")
                failed += 1

        return {
            "processed": processed,
            "skipped": skipped,
            "failed": failed,
            "total": len(sessions)
        }
