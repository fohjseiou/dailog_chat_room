from typing import List
from langchain_community.embeddings import DashScopeEmbeddings
from app.config import get_settings
import logging
import asyncio

logger = logging.getLogger(__name__)

# Custom exceptions
class EmbeddingServiceError(Exception):
    """Base exception for embedding service errors"""
    pass


class EmbeddingAPIError(EmbeddingServiceError):
    """Raised when the embedding API returns an error"""
    pass


class EmbeddingService:
    """Service for generating text embeddings using LangChain DashScope"""

    def __init__(self):
        settings = get_settings()
        # 使用 LangChain 的 DashScope Embeddings
        self.embeddings = DashScopeEmbeddings(
            model=settings.dashscope_embedding_model,
            dashscope_api_key=settings.dashscope_api_key
        )

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Input text to embed

        Returns:
            List of embedding values

        Raises:
            ValueError: If text is empty or None
        """
        # Input validation
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # LangChain DashScopeEmbeddings.embed_query 返回 List[float]
        try:
            # LangChain's embed_query is synchronous, run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.embeddings.embed_query(text)
            )
            return result
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise EmbeddingServiceError(f"Failed to generate embedding: {e}") from e

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts with retry logic

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        max_retries = 3
        base_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                # LangChain DashScopeEmbeddings 自动处理批量
                # 返回 List[List[float]]
                # LangChain's embed_documents is synchronous, run in thread pool
                loop = asyncio.get_event_loop()
                results = await loop.run_in_executor(
                    None,
                    lambda: self.embeddings.embed_documents(texts)
                )
                return results
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"Embedding batch attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay} seconds..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Error generating batch embeddings after {max_retries} attempts: {e}")
                    raise EmbeddingServiceError(f"Failed to generate batch embeddings: {e}") from e


# Singleton
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the embedding service singleton"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
