from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # Database
    database_url: str
    database_url_sync: str

    # DashScope / Qwen
    dashscope_api_key: str
    dashscope_model: str = "qwen-plus"
    dashscope_embedding_model: str = "text-embedding-v3"

    # ChromaDB
    chroma_db_path: str = "./data/chroma"

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True
    cors_origins: str = "http://localhost:5173"

    # Summary
    summary_message_threshold: int = 10
    summary_token_threshold: int = 8000

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"


@lru_cache(maxsize=None)
def get_settings() -> Settings:
    return Settings()
