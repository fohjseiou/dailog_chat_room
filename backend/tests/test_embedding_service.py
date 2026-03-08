import pytest
from app.services.embedding_service import get_embedding_service


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
