import pytest
from app.services.chroma_service import get_chroma_service

@pytest.mark.asyncio
async def test_chroma_singleton():
    """Test singleton pattern"""
    service1 = get_chroma_service()
    service2 = get_chroma_service()
    assert service1 is service2

@pytest.mark.asyncio
async def test_add_and_search():
    """Test adding and searching documents"""
    service = get_chroma_service()
    from app.services.embedding_service import get_embedding_service

    emb_service = get_embedding_service()
    embedding = await emb_service.generate_embedding("test doc")

    await service.add_documents(
        documents=["Test document"],
        embeddings=[embedding],
        metadatas=[{"category": "test", "source": "test"}],
        ids=["test_1"]
    )

    results = await service.search(embedding, n_results=1)
    assert len(results["documents"]) == 1
