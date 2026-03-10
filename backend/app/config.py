"""Application configuration with multi-provider LLM support."""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel


class Settings(BaseSettings):
    # Database
    database_url: str
    database_url_sync: str

    # DashScope / Qwen (default provider)
    dashscope_api_key: str
    dashscope_model: str = "qwen-plus"
    dashscope_embedding_model: str = "text-embedding-v3"

    # OpenAI (optional, for future multi-provider support)
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"

    # LLM Provider selection
    llm_provider: str = "tongyi"  # tongyi | openai

    # ChromaDB
    chroma_db_path: str = "./data/chroma"
    chroma_collection_name: str = "legal_knowledge"
    chroma_persistent_storage: bool = True

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True
    cors_origins: str = "http://localhost:5173"

    # Summary
    summary_message_threshold: int = 10
    summary_token_threshold: int = 8000

    # Auth
    secret_key: str
    password_min_length: int = 6
    jwt_expire_days: int = 7

    # Memory
    short_term_session_limit: int = 3
    long_term_memory_top_k: int = 5
    enable_memory_extraction: bool = True

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    model_config = ConfigDict(env_file=".env")


def create_llm_from_config(settings: Settings) -> BaseChatModel:
    """
    Create LLM instance based on configuration.

    Args:
        settings: Application settings

    Returns:
        Configured LLM instance

    Raises:
        ValueError: If provider is not supported
    """
    provider = settings.llm_provider.lower()

    if provider == "tongyi":
        return ChatTongyi(
            model=settings.dashscope_model,
            dashscope_api_key=settings.dashscope_api_key,
            temperature=0.7,
        )
    elif provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required when provider is 'openai'")
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.7,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


@lru_cache(maxsize=None)
def get_settings() -> Settings:
    return Settings()
