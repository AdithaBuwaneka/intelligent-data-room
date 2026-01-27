"""
Application configuration using Pydantic Settings.
Loads environment variables from .env file.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    gemini_api_key: str

    # MongoDB
    mongodb_uri: str

    # ImageKit
    imagekit_public_key: str
    imagekit_private_key: str
    imagekit_url_endpoint: str

    # Application
    debug: bool = False
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    # File upload limits
    max_file_size_mb: int = 10

    # Context retention
    max_context_messages: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse allowed origins string into list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.max_file_size_mb * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
