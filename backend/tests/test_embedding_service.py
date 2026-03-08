import pytest
from app.services.embedding_service import (
    get_embedding_service,
    EmbeddingServiceError,
    EmbeddingAPIError
)


@pytest.mark.asyncio
async def test_generate_embedding():
    """Test single DashScope embedding generation"""
    service = get_embedding_service()
    embedding = await service.generate_embedding("测试文本")
    assert embedding is not None
    assert len(embedding) > 0
    # DashScope text-embedding-v3 typically outputs 1024 dimensions


@pytest.mark.asyncio
async def test_batch_embeddings():
    """Test batch DashScope embedding generation"""
    service = get_embedding_service()
    embeddings = await service.generate_embeddings_batch([
        "文本1", "文本2", "文本3"
    ])
    assert len(embeddings) == 3
    assert all(len(emb) > 0 for emb in embeddings)


@pytest.mark.asyncio
async def test_embedding_dimensions():
    """Test that embeddings have consistent dimensions"""
    service = get_embedding_service()
    embedding1 = await service.generate_embedding("第一段文本")
    embedding2 = await service.generate_embedding("第二段文本")
    assert len(embedding1) == len(embedding2)
    # text-embedding-v3 should output 1024 dimensions
    assert len(embedding1) == 1024


@pytest.mark.asyncio
async def test_empty_text():
    """Test that empty text raises ValueError"""
    service = get_embedding_service()
    with pytest.raises(ValueError, match="cannot be empty"):
        await service.generate_embedding("")


@pytest.mark.asyncio
async def test_whitespace_only_text():
    """Test that whitespace-only text raises ValueError"""
    service = get_embedding_service()
    with pytest.raises(ValueError, match="cannot be empty"):
        await service.generate_embedding("   ")


@pytest.mark.asyncio
async def test_singleton():
    """Test that embedding service returns singleton instance"""
    service1 = get_embedding_service()
    service2 = get_embedding_service()
    assert service1 is service2


@pytest.mark.asyncio
async def test_custom_exceptions_exist():
    """Test that custom exception types are available"""
    # Test that we can import and use the custom exceptions
    assert EmbeddingServiceError is not None
    assert EmbeddingAPIError is not None
    # EmbeddingAPIError should inherit from EmbeddingServiceError
    assert issubclass(EmbeddingAPIError, EmbeddingServiceError)
