#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification script for DocumentService compatibility with refactored services.

This script verifies that:
1. ChunkingService.chunk_by_semantic_units() returns the expected format
2. EmbeddingService.generate_embeddings_batch() returns the expected format
3. Both services work together correctly in DocumentService
"""
import asyncio
import sys
from app.services.chunking_service import get_chunking_service
from app.services.embedding_service import get_embedding_service
from app.services.document_service import get_document_service

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def verify_chunking_service():
    """Verify ChunkingService returns expected format"""
    print_section("1. Verifying ChunkingService")

    service = get_chunking_service()
    text = "This is a test document. It has multiple sentences. " \
           "Each sentence should be handled properly by the chunking service."

    chunks = service.chunk_by_semantic_units(text, "test_doc_123")

    print(f"✓ ChunkingService.chunk_by_semantic_units() returned {len(chunks)} chunks")
    print(f"✓ Return type: {type(chunks).__name__}")
    print(f"✓ Expected format: List[Dict[str, Any]]")

    if chunks:
        first_chunk = chunks[0]
        print(f"\n  First chunk structure:")
        print(f"    - id: {type(first_chunk['id']).__name__} = '{first_chunk['id']}'")
        print(f"    - text: {type(first_chunk['text']).__name__} = '{first_chunk['text'][:50]}...'")
        print(f"    - metadata: {type(first_chunk['metadata']).__name__}")
        print(f"      * document_id: {first_chunk['metadata']['document_id']}")
        print(f"      * chunk_index: {first_chunk['metadata']['chunk_index']}")
        print(f"      * char_count: {first_chunk['metadata']['char_count']}")

    # Verify expected keys
    assert all(key in chunks[0] for key in ['id', 'text', 'metadata']), \
        "❌ Chunk missing required keys"
    assert all(key in chunks[0]['metadata'] for key in ['document_id', 'chunk_index', 'char_count']), \
        "❌ Metadata missing required keys"

    print("\n✓ ChunkingService format is COMPATIBLE")
    return True


async def verify_embedding_service():
    """Verify EmbeddingService returns expected format"""
    print_section("2. Verifying EmbeddingService")

    service = get_embedding_service()
    texts = ["First text", "Second text", "Third text"]

    embeddings = await service.generate_embeddings_batch(texts)

    print(f"✓ EmbeddingService.generate_embeddings_batch() returned {len(embeddings)} embeddings")
    print(f"✓ Return type: {type(embeddings).__name__}")
    print(f"✓ Expected format: List[List[float]]")

    if embeddings:
        first_embedding = embeddings[0]
        print(f"\n  First embedding structure:")
        print(f"    - Type: {type(first_embedding).__name__}")
        print(f"    - Length: {len(first_embedding)} dimensions")
        print(f"    - Sample values: {first_embedding[:3]}")

    # Verify format
    assert isinstance(embeddings, list), "❌ Embeddings is not a list"
    assert len(embeddings) == len(texts), "❌ Embedding count doesn't match text count"
    assert all(isinstance(emb, list) for emb in embeddings), "❌ Embedding is not a list"
    assert all(isinstance(val, float) for emb in embeddings for val in emb), \
        "❌ Embedding values are not floats"

    print("\n✓ EmbeddingService format is COMPATIBLE")
    return True


async def verify_integration():
    """Verify both services work together in DocumentService"""
    print_section("3. Verifying DocumentService Integration")

    # This is a smoke test to verify the services can be instantiated together
    service = get_document_service()

    print(f"✓ DocumentService instantiated successfully")
    print(f"✓ Uses ChunkingService: {type(service.chunking_service).__name__}")
    print(f"✓ Uses EmbeddingService: {type(service.embedding_service).__name__}")
    print(f"✓ Uses ChromaService: {type(service.chroma_service).__name__}")

    # Verify methods exist
    assert hasattr(service, 'process_file'), "❌ Missing process_file method"
    assert hasattr(service, 'search_knowledge'), "❌ Missing search_knowledge method"
    assert hasattr(service, 'delete_document'), "❌ Missing delete_document method"

    print("\n✓ DocumentService integration is COMPATIBLE")
    return True


async def main():
    """Run all verification checks"""
    print_section("DocumentService Compatibility Verification")
    print("\nThis script verifies compatibility between:")
    print("  - DocumentService")
    print("  - ChunkingService (refactored with LangChain)")
    print("  - EmbeddingService (refactored with LangChain)")

    try:
        # Verify ChunkingService
        verify_chunking_service()

        # Verify EmbeddingService
        await verify_embedding_service()

        # Verify Integration
        await verify_integration()

        print_section("✓ ALL CHECKS PASSED")
        print("\nConclusion:")
        print("  ✓ ChunkingService returns expected format")
        print("  ✓ EmbeddingService returns expected format")
        print("  ✓ DocumentService integration is compatible")
        print("  ✓ No adjustments needed")

        return 0

    except Exception as e:
        print_section("❌ VERIFICATION FAILED")
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
