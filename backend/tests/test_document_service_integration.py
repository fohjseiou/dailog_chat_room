"""
Integration test to verify DocumentService works with refactored ChunkingService and EmbeddingService
"""
import pytest
import tempfile
from pathlib import Path
from app.services.document_service import get_document_service


class TestDocumentServiceIntegration:
    """Test DocumentService integration with LangChain-based services"""

    @pytest.mark.asyncio
    async def test_process_txt_file(self):
        """Test processing a TXT file through DocumentService"""
        # Create a temporary test file
        content = "This is a test document. It contains multiple sentences. " \
                  "The purpose is to test the integration between DocumentService, " \
                  "ChunkingService, and EmbeddingService. All services have been " \
                  "refactored to use LangChain."

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            # Process the file
            service = get_document_service()
            result = await service.process_file(
                file_path=temp_path,
                title="Test Document",
                category="law",
                source="test_source"
            )

            # Verify the result
            assert result["title"] == "Test Document"
            assert result["category"] == "law"
            assert result["source"] == "test_source"
            assert result["chunk_count"] > 0
            assert "document_id" in result

            # Verify chunks were created
            assert result["chunk_count"] > 0

        finally:
            # Clean up
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_chunking_service_compatibility(self):
        """Test that ChunkingService returns expected format"""
        from app.services.chunking_service import get_chunking_service

        service = get_chunking_service()
        text = "This is a test. It has multiple sentences. Each sentence should be handled properly."

        chunks = service.chunk_by_semantic_units(text, "test_doc")

        # Verify format
        assert isinstance(chunks, list)
        assert len(chunks) > 0

        for chunk in chunks:
            assert "id" in chunk
            assert "text" in chunk
            assert "metadata" in chunk
            assert isinstance(chunk["id"], str)
            assert isinstance(chunk["text"], str)
            assert isinstance(chunk["metadata"], dict)
            assert "document_id" in chunk["metadata"]
            assert "chunk_index" in chunk["metadata"]
            assert "char_count" in chunk["metadata"]

    @pytest.mark.asyncio
    async def test_embedding_service_compatibility(self):
        """Test that EmbeddingService returns expected format"""
        from app.services.embedding_service import get_embedding_service

        service = get_embedding_service()
        texts = ["First text", "Second text", "Third text"]

        embeddings = await service.generate_embeddings_batch(texts)

        # Verify format
        assert isinstance(embeddings, list)
        assert len(embeddings) == len(texts)

        for embedding in embeddings:
            assert isinstance(embedding, list)
            assert all(isinstance(x, float) for x in embedding)
            # DashScope embeddings are typically 1024 or 1536 dimensions
            assert len(embedding) > 0

    @pytest.mark.asyncio
    async def test_search_knowledge(self):
        """Test searching knowledge base"""
        # Create a temporary test file
        content = "Legal contract terms and conditions. This document contains " \
                  "important legal information about contracts and agreements."

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            # Process the file first
            service = get_document_service()
            await service.process_file(
                file_path=temp_path,
                title="Contract Document",
                category="contract",
                source="test"
            )

            # Search for relevant content
            results = await service.search_knowledge(
                query="legal contracts",
                category="contract",
                n_results=3
            )

            # Verify results
            assert isinstance(results, list)
            assert len(results) > 0

            for result in results:
                assert "text" in result
                assert "metadata" in result
                assert "score" in result
                assert "distance" in result
                assert isinstance(result["text"], str)
                assert isinstance(result["metadata"], dict)
                assert isinstance(result["score"], float)
                assert isinstance(result["distance"], float)

        finally:
            # Clean up
            Path(temp_path).unlink()
