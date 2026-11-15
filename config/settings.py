
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "Mittelstand AI"
    app_environment: str = "development"
    debug: bool = False

    # Database
    database_url: str = "dbname=mittelstand_ai"
    database_connect_timeout: int = Field(default=10, gt=0)

    # Ollama generation
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:1.5b"
    ollama_timeout: int = Field(default=180, gt=0)

    # Ollama embeddings
    embedding_model: str = "nomic-embed-text"
    embedding_dimensions: int = Field(default=768, gt=0)

    # Document uploads
    max_upload_size: int = Field(
        default=10 * 1024 * 1024,
        gt=0,
    )
    upload_directory: str = "data/uploads"

    # Vector database
    vector_store_directory: str = "data/vector_store"
    vector_collection_name: str = "mittelstand_documents"


@lru_cache
def get_settings() -> Settings:
    """Return a cached application settings instance."""
    return Settings()


settings = get_settings()
