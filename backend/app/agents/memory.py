"""Memory management for agent conversation history.

This module provides factory methods for creating different types
of conversation memory for the agent.
"""

from langchain.memory import ConversationBufferMemory
from langchain_core.memory import BaseMemory
import logging

logger = logging.getLogger(__name__)


class MemoryFactory:
    """
    Factory for creating different types of conversation memory.

    This class provides a unified interface for creating various
    memory implementations, with plans for future expansion.
    """

    @staticmethod
    def create_buffer_memory() -> BaseMemory:
        """
        Create a buffer memory that stores all conversation history.

        Returns:
            ConversationBufferMemory instance configured for agent use
        """
        return ConversationBufferMemory(
            return_messages=True,
            output_key="response"
        )

    # Placeholders for future memory types
    @staticmethod
    def create_window_memory(k: int = 5):
        """
        Create a window memory that keeps only the last k exchanges.

        TODO: Implement window memory
        """
        raise NotImplementedError("Window memory not yet implemented")

    @staticmethod
    def create_summary_memory():
        """
        Create a summary memory that maintains conversation summaries.

        TODO: Implement summary memory
        """
        raise NotImplementedError("Summary memory not yet implemented")
