"""Service for extracting and storing long-term memories from conversations."""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.session import Session as SessionModel
from app.models.message import Message
from app.services.memory_service import MemoryService
from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)

# Keywords that might indicate user facts
FACT_KEYWORDS = [
    "我是", "我叫", "我的名字", "我的工作", "我是做",
    "我喜欢", "我偏好", "我希望", "我想要",
    "我的职业", "我的专业", "我从事",
]

# Prompts
USER_FACT_EXTRACTION_PROMPT = """从以下对话中提取关于用户的具体事实信息（个人信息、偏好、职业背景等）。

只提取明确提到的信息，不要推测。如果没有明确信息，返回"无"。

对话：
{conversation_text}

返回格式（JSON）：
{{
    "facts": [
        {{
            "fact": "用户是执业律师，专精合同法",
            "confidence": "high"
        }},
        {{
            "fact": "用户偏好简洁专业的回答",
            "confidence": "medium"
        }}
    ]
}}

如果没有任何明确信息，返回：{{"facts": []}}"""

CONVERSATION_SUMMARY_PROMPT = """请将以下对话总结为简洁的摘要，用于后续检索。

摘要要求：
1. 突出用户的主要问题和需求
2. 总结提供的法律信息要点
3. 保留重要的细节（金额、时间、相关方等）
4. 简洁明了，2-4句话
5. 使用中文输出

对话：
{conversation_text}

摘要："""


class MemoryExtractionService:
    """Service for extracting and storing long-term memories"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.memory_service = MemoryService(db)
        self.llm_service = get_llm_service()

    async def extract_and_store_facts(
        self,
        user_id: str,
        session_id: str,
        conversation_text: str
    ) -> List[str]:
        """
        Extract user facts from conversation and store to ChromaDB.

        Args:
            user_id: User identifier
            session_id: Current session ID
            conversation_text: Recent conversation text

        Returns:
            List of extracted facts
        """
        try:
            # Use LLM to extract facts
            prompt = USER_FACT_EXTRACTION_PROMPT.format(conversation_text=conversation_text)

            response = await self.llm_service.generate_response(
                message=prompt,
                conversation_history=[],
                system_prompt="你是用户信息提取专家，负责从对话中提取用户相关事实。"
            )

            # Parse response (simple JSON extraction)
            import json
            try:
                # Clean response
                # 提取出来我们需要的json数据
                response = response.strip()
                if response.startswith("```json"):
                    response = response[7:]
                if response.startswith("```"):
                    response = response[3:]
                if response.endswith("```"):
                    response = response[:-3]
                response = response.strip()

                result = json.loads(response)
                facts = result.get("facts", [])
            except json.JSONDecodeError:
                # Fallback: simple line-by-line extraction
                facts = []
                for line in response.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("{{") and not line.startswith("}}"):
                        facts.append({"fact": line, "confidence": "low"})

            stored_facts = []
            for fact_item in facts:
                if isinstance(fact_item, dict):
                    fact_text = fact_item.get("fact", "")
                    confidence = fact_item.get("confidence", "medium")

                    if fact_text and fact_text != "无":
                        # Store to ChromaDB
                        metadata = {
                            "type": "user_fact",
                            "confidence": confidence,
                            "session_id": session_id,
                        }
                        await self.memory_service.save_user_fact(user_id, fact_text, metadata)
                        stored_facts.append(fact_text)
                        logger.info(f"Stored user fact: {fact_text[:50]}...")

            return stored_facts

        except Exception as e:
            logger.error(f"Error extracting user facts: {e}")
            return []

    async def generate_and_store_summary(
        self,
        user_id: str,
        session_id: str
    ) -> Optional[str]:
        """
        Generate conversation summary and store to ChromaDB.

        Args:
            user_id: User identifier
            session_id: Session ID

        Returns:
            Generated summary or None
        """
        try:
            # Get session with messages
            result = await self.db.execute(
                select(SessionModel)
                .options(selectinload(SessionModel.messages))
                .where(SessionModel.id == session_id)
            )
            session = result.scalar_one_or_none()

            if not session or not session.messages:
                logger.warning(f"Session {session_id} not found or has no messages")
                return None

            # Build conversation text
            conversation_parts = []
            for msg in session.messages[-20:]:  # Last 20 messages
                role = "用户" if msg.role == "user" else "助手"
                conversation_parts.append(f"{role}：{msg.content}")

            conversation_text = "\n".join(conversation_parts)

            # Generate summary using LLM
            prompt = CONVERSATION_SUMMARY_PROMPT.format(conversation_text=conversation_text)

            summary = await self.llm_service.generate_response(
                message=prompt,
                conversation_history=[],
                system_prompt="你是对话摘要专家，负责为长期记忆存储生成简洁摘要。"
            )

            summary = summary.strip()

            # Remove common prefixes
            for prefix in ["摘要：", "摘要:", "Summary:", "【摘要】", "摘要: "]:
                if summary.startswith(prefix):
                    summary = summary[len(prefix):].strip()

            # Store to ChromaDB
            await self.memory_service.save_conversation_summary(user_id, session_id, summary)

            # Also update session summary in DB
            session.summary = summary
            await self.db.commit()

            logger.info(f"Stored conversation summary for session {session_id}: {summary[:50]}...")
            return summary

        except Exception as e:
            logger.error(f"Error generating conversation summary: {e}")
            return None

    def should_extract_facts(self, message: str) -> bool:
        """Check if message contains potential user facts."""
        return any(keyword in message for keyword in FACT_KEYWORDS)

    async def process_conversation_memory(
        self,
        user_id: str,
        session_id: str,
        message_count: int,
        last_user_message: str,
        last_n_messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Process conversation for memory extraction based on triggers.

        Args:
            user_id: User identifier
            session_id: Session ID
            message_count: Current message count in session
            last_user_message: Last user message content
            last_n_messages: Last N messages for context

        Returns:
            Dict with extraction results
        """
        results = {
            "facts_extracted": [],
            "summary_generated": None,
        }

        if not user_id:
            return results

        try:
            # Build conversation text from last N messages
            conversation_text = "\n".join([
                f"{msg['role']}：{msg['content']}"
                for msg in last_n_messages
            ])

            # Trigger 1: Check for user fact keywords
            if self.should_extract_facts(last_user_message):
                facts = await self.extract_and_store_facts(
                    user_id, session_id, conversation_text
                )
                results["facts_extracted"] = facts

            # Trigger 2: Every 10 rounds - extract facts as supplement
            if message_count % 10 == 0:
                facts = await self.extract_and_store_facts(
                    user_id, session_id, conversation_text
                )
                if facts:
                    results["facts_extracted"].extend(facts)

            # Trigger 3: Every 10 rounds - generate summary
            if message_count % 10 == 0:
                summary = await self.generate_and_store_summary(user_id, session_id)
                results["summary_generated"] = summary

            return results

        except Exception as e:
            logger.error(f"Error processing conversation memory: {e}")
            return results
