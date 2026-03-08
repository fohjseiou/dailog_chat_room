from typing import List
import dashscope
from dashscope import TextEmbedding
from app.config import get_settings
import logging
import asyncio

logger = logging.getLogger(__name__)

# Constants
DEFAULT_TEXT_TYPE = "document"

# Custom exceptions
class EmbeddingServiceError(Exception):
    """Base exception for embedding service errors"""
    pass


class EmbeddingAPIError(EmbeddingServiceError):
    """Raised when the embedding API returns an error"""
    pass


class EmbeddingService:
    """Service for generating text embeddings using DashScope"""

    def __init__(self):
        settings = get_settings()
        dashscope.api_key = settings.dashscope_api_key
        self.model = settings.dashscope_embedding_model

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text using DashScope

        Args:
            text: Input text to embed

        Returns:
            List of embedding values

        Raises:
            ValueError: If text is empty or None
            EmbeddingAPIError: If the DashScope API returns an error
        """
        # Input validation
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        try:
            # DashScope TextEmbedding API is synchronous, run in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: TextEmbedding.call(
                    model=self.model,
                    input=text,
                    text_type=DEFAULT_TEXT_TYPE
                )
            )

            if response.status_code != 200:
                logger.error(f"DashScope TextEmbedding API error: {response.code} - {response.message}")
                raise EmbeddingAPIError(f"Embedding API error: {response.message}")

            # DashScope returns embeddings in output.embedding
            return response.output['embeddings'][0]['embedding']
        except Exception as e:
            logger.error(f"Error generating DashScope embedding: {e}")
            raise EmbeddingServiceError(f"Failed to generate embedding: {e}") from e

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        try:
            # DashScope supports batch embedding
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: TextEmbedding.call(
                    model=self.model,
                    input=texts,
                    text_type=DEFAULT_TEXT_TYPE
                )
            )

            if response.status_code != 200:
                logger.error(f"DashScope TextEmbedding API error: {response.code} - {response.message}")
                raise EmbeddingAPIError(f"Batch embedding API error: {response.message}")

            return [item['embedding'] for item in response.output['embeddings']]
        except Exception as e:
            logger.warning(f"Batch embedding failed, falling back to sequential: {e}")
            # Fallback to sequential generation
            embeddings = []
            for text in texts:
                emb = await self.generate_embedding(text)
                embeddings.append(emb)
            return embeddings


# Singleton
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the embedding service singleton"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
