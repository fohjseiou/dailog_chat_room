"""Tests for MemoryFactory."""

import pytest
from app.agents.memory import MemoryFactory


def test_create_buffer_memory():
    """Test creating buffer memory."""
    memory = MemoryFactory.create_buffer_memory()
    assert memory is not None
    # Verify it's the right type
    from langchain.memory import ConversationBufferMemory
    assert isinstance(memory, ConversationBufferMemory)


def test_buffer_memory_config():
    """Test buffer memory has correct configuration."""
    memory = MemoryFactory.create_buffer_memory()
    assert memory.return_messages == True
    assert memory.output_key == "response"
