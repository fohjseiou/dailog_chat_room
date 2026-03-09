import pytest
from pathlib import Path
import sys
sys.path.insert(0, '.')

from app.services.chunking_service import ChunkingService


def test_chunk_basic_text():
    """测试基本文本切分"""
    service = ChunkingService()
    text = "这是第一段。\n\n这是第二段。\n\n这是第三段。"
    chunks = service.chunk_by_semantic_units(text, "test_doc")

    assert len(chunks) > 0
    assert all("text" in chunk for chunk in chunks)
    assert all("metadata" in chunk for chunk in chunks)
    assert all("id" in chunk for chunk in chunks)


def test_chunk_returns_metadata():
    """测试返回的 chunks 包含正确元数据"""
    service = ChunkingService()
    text = "测试文本内容用于验证元数据"
    chunks = service.chunk_by_semantic_units(text, "test_doc")

    for chunk in chunks:
        assert chunk["metadata"]["document_id"] == "test_doc"
        assert "chunk_index" in chunk["metadata"]
        assert isinstance(chunk["metadata"]["chunk_index"], int)


def test_chunk_empty_text():
    """测试空文本处理"""
    service = ChunkingService()
    chunks = service.chunk_by_semantic_units("", "test_doc")
    assert chunks == []


def test_chunk_size_limit():
    """测试 chunk 大小限制"""
    service = ChunkingService(chunk_size=100)
    # 创建一个大于 100 字符的文本
    text = "word" * 50  # 200 字符
    chunks = service.chunk_by_semantic_units(text, "test_doc")

    # 每个 chunk 应该不超过 chunk_size（稍微允许溢出以保持语义完整性）
    for chunk in chunks:
        assert len(chunk["text"]) <= 150  # 允许 50% 溢出
