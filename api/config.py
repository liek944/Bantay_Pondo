"""Configuration settings for Bantay Pondo."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    postgres_user: str = "bantay"
    postgres_password: str = "bantay_secret"
    postgres_db: str = "bantay_pondo"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    database_url: str = "postgresql+psycopg://bantay:bantay_secret@localhost:5432/bantay_pondo"
    database_url_async: str = (
        "postgresql+psycopg_async://bantay:bantay_secret@localhost:5432/bantay_pondo"
    )

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_url: str = "redis://localhost:6379/0"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    data_version: str = "v1.0.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
