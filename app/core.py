from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Financial Document Management System"
    environment: str = "dev"
    debug: bool = Field(default=False, validation_alias="APP_DEBUG")
    database_url: str = "sqlite:///./financial_docs.db"
    jwt_secret_key: str = Field(default="change-me-in-production")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    upload_dir: Path = Path("storage/documents")
    vector_backend: Literal["sql", "qdrant"] = "sql"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "financial_documents"
    embedding_provider: Literal["hash", "sentence-transformers", "openai"] = "hash"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    openai_api_key: str | None = None
    chunk_size: int = 900
    chunk_overlap: int = 150

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    return settings
