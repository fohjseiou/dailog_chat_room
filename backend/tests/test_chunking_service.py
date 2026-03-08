import pytest
from app.services.chunking_service import get_chunking_service

def test_basic_chunking():
    """Test basic text chunking"""
    service = get_chunking_service()
    text = "这是一段测试文本。" * 100
    chunks = service.chunk_text(text, "test_doc")
    assert len(chunks) > 1
    assert all("text" in chunk for chunk in chunks)

def test_semantic_chunking():
    """Test semantic unit chunking"""
    service = get_chunking_service()
    text = """第一段内容。

第二段内容。

第三段内容。""" * 10
    chunks = service.chunk_by_semantic_units(text, "test_doc")
    assert len(chunks) > 0
