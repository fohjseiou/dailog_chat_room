import pytest
from app.agents.utils import convert_to_langchain_messages, convert_to_dict_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

def test_convert_user_message():
    """Test converting user message to LangChain format"""
    history = [{"role": "user", "content": "Hello"}]
    result = convert_to_langchain_messages(history)
    assert len(result) == 1
    assert isinstance(result[0], HumanMessage)
    assert result[0].content == "Hello"

def test_convert_assistant_message():
    """Test converting assistant message to LangChain format"""
    history = [{"role": "assistant", "content": "Hi there"}]
    result = convert_to_langchain_messages(history)
    assert len(result) == 1
    assert isinstance(result[0], AIMessage)
    assert result[0].content == "Hi there"

def test_convert_mixed_messages():
    """Test converting mixed conversation history"""
    history = [
        {"role": "user", "content": "Question"},
        {"role": "assistant", "content": "Answer"},
        {"role": "user", "content": "Follow-up"}
    ]
    result = convert_to_langchain_messages(history)
    assert len(result) == 3
    assert isinstance(result[0], HumanMessage)
    assert isinstance(result[1], AIMessage)
    assert isinstance(result[2], HumanMessage)

def test_convert_back_to_dict():
    """Test converting LangChain messages back to dict format"""
    messages = [HumanMessage(content="Hello"), AIMessage(content="Hi")]
    result = convert_to_dict_messages(messages)
    assert result == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"}
    ]
