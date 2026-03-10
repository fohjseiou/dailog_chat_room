"""Utility functions for LangChain message conversion."""

from typing import List, Dict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage


def convert_to_langchain_messages(history: List[Dict[str, str]]) -> List[BaseMessage]:
    """
    Convert dict-based message history to LangChain BaseMessage format.

    Args:
        history: List of messages with 'role' and 'content' keys

    Returns:
        List of LangChain BaseMessage objects
    """
    messages = []
    for msg in history:
        role = msg.get("role")
        content = msg.get("content", "")

        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
        elif role == "system":
            messages.append(SystemMessage(content=content))
        # Ignore unknown roles

    return messages


def convert_to_dict_messages(messages: List[BaseMessage]) -> List[Dict[str, str]]:
    """
    Convert LangChain BaseMessage format to dict-based format.

    Args:
        messages: List of LangChain BaseMessage objects

    Returns:
        List of messages with 'role' and 'content' keys
    """
    result = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            result.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            result.append({"role": "assistant", "content": msg.content})
        elif isinstance(msg, SystemMessage):
            result.append({"role": "system", "content": msg.content})
    return result
