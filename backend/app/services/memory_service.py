"""Service for managing user memory (short-term and long-term)"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.models.session import Session
from app.models.message import Message
from app.models.user_preference import UserPreference
from app.services.chroma_service import get_chroma_service
from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class MemoryService:
    """Service for managing user short-term and long-term memory"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._chroma_service = get_chroma_service()

    async def get_short_term_context(
        self,
        user_id: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get last N sessions for user (short-term context).

        Args:
            user_id: User identifier
            limit: Number of recent sessions to retrieve

        Returns:
            List of session dictionaries with messages
        """
        try:
            # Get recent sessions for user
            result = await self.db.execute(
                select(Session)
                .options(selectinload(Session.messages))
                .where(Session.user_id == user_id)
                .order_by(Session.updated_at.desc())
                .limit(limit)
            )
            sessions = result.scalars().all()

            # Format context
            context = []
            for session in sessions:
                messages = [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "created_at": msg.created_at.isoformat()
                    }
                    for msg in session.messages
                ]

                context.append({
                    "session_id": session.id,
                    "title": session.title,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "message_count": session.message_count,
                    "messages": messages
                })

            return context
        except Exception as e:
            logger.error(f"Error getting short-term context for user {user_id}: {e}")
            return []

    async def get_long_term_memory(
        self,
        user_id: str,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get facts/summaries from ChromaDB for user.

        Args:
            user_id: User identifier
            query: Query text for semantic search
            top_k: Number of results to retrieve

        Returns:
            List of memory items with facts and metadata
        """
        try:
            # Get embedding service
            embedding_service = get_embedding_service()
            if embedding_service is None:
                logger.warning("Embedding service unavailable, returning empty long-term memory")
                return []

            # Generate query embedding
            query_embedding = await embedding_service.generate_embedding(query)

            # Search ChromaDB
            results = await self._chroma_service.search(
                query_embedding=query_embedding,
                n_results=top_k,
                where={"user_id": user_id}
            )

            # Filter and format results
            memories = []
            for i, doc in enumerate(results.get("documents", [])):
                metadata = results.get("metadatas", [{}])[i] if i < len(results.get("metadatas", [])) else {}
                distance = results.get("distances", [])[i] if i < len(results.get("distances", [])) else None

                # Ensure the memory belongs to the user
                if metadata.get("user_id") == user_id:
                    memories.append({
                        "fact": doc,
                        "metadata": metadata,
                        "distance": distance
                    })

            return memories
        except Exception as e:
            logger.error(f"Error getting long-term memory for user {user_id}: {e}")
            return []

    async def save_user_fact(
        self,
        user_id: str,
        fact: str,
        metadata: Dict[str, Any]
    ) -> None:
        """
        Save a user fact to ChromaDB.

        Args:
            user_id: User identifier
            fact: Fact text to store
            metadata: Additional metadata (type, confidence, etc.)
        """
        try:
            # Get embedding service
            embedding_service = get_embedding_service()
            if embedding_service is None:
                logger.warning("Embedding service unavailable, skipping fact save")
                return

            # Generate embedding
            embedding = await embedding_service.generate_embedding(fact)

            # Add user_id to metadata
            fact_metadata = {
                **metadata,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }

            # Generate unique ID
            fact_id = f"fact_{user_id}_{datetime.utcnow().timestamp()}"

            # Save to ChromaDB
            await self._chroma_service.add_documents(
                documents=[fact],
                embeddings=[embedding],
                metadatas=[fact_metadata],
                ids=[fact_id]
            )

            logger.info(f"Saved fact for user {user_id}: {fact[:50]}...")
        except Exception as e:
            logger.error(f"Error saving user fact: {e}")
            raise

    async def save_conversation_summary(
        self,
        user_id: str,
        session_id: str,
        summary: str
    ) -> None:
        """
        Save a conversation summary to ChromaDB.

        Args:
            user_id: User identifier
            session_id: Session identifier
            summary: Summary text to store
        """
        try:
            # Get embedding service
            embedding_service = get_embedding_service()
            if embedding_service is None:
                logger.warning("Embedding service unavailable, skipping summary save")
                return

            # Generate embedding
            embedding = await embedding_service.generate_embedding(summary)

            # Prepare metadata
            summary_metadata = {
                "user_id": user_id,
                "session_id": session_id,
                "type": "summary",
                "timestamp": datetime.utcnow().isoformat()
            }

            # Generate unique ID
            summary_id = f"summary_{user_id}_{session_id}_{datetime.utcnow().timestamp()}"

            # Save to ChromaDB
            await self._chroma_service.add_documents(
                documents=[summary],
                embeddings=[embedding],
                metadatas=[summary_metadata],
                ids=[summary_id]
            )

            logger.info(f"Saved summary for user {user_id}, session {session_id}")
        except Exception as e:
            logger.error(f"Error saving conversation summary: {e}")
            raise

    async def get_preferences(self, user_id: str) -> Dict[str, str]:
        """
        Get all preferences for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary of preference key-value pairs
        """
        try:
            result = await self.db.execute(
                select(UserPreference).where(UserPreference.user_id == user_id)
            )
            preferences = result.scalars().all()

            return {pref.key: pref.value for pref in preferences}
        except Exception as e:
            logger.error(f"Error getting preferences for user {user_id}: {e}")
            return {}

    async def set_preference(
        self,
        user_id: str,
        key: str,
        value: str
    ) -> None:
        """
        Save or update a user preference.

        Args:
            user_id: User identifier
            key: Preference key
            value: Preference value
        """
        try:
            # Check if preference exists
            result = await self.db.execute(
                select(UserPreference).where(
                    and_(UserPreference.user_id == user_id, UserPreference.key == key)
                )
            )
            preference = result.scalar_one_or_none()

            if preference:
                # Update existing preference
                preference.value = value
            else:
                # Create new preference
                preference = UserPreference(user_id=user_id, key=key, value=value)
                self.db.add(preference)

            await self.db.commit()
            logger.info(f"Set preference {key}={value} for user {user_id}")
        except Exception as e:
            logger.error(f"Error setting preference: {e}")
            await self.db.rollback()
            raise
