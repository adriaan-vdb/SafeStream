"""SafeStream configuration management.

Centralizes application settings using Pydantic Settings for type safety
and environment variable management.
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Database Configuration
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/safestream.db",
        description="Database connection URL",
    )

    db_echo: bool = Field(
        default=False,
        description="Enable SQLAlchemy query logging",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",  # Ignore extra fields from environment
    }


# Global settings instance
settings = Settings()

# Ensure data directory exists for SQLite
if settings.database_url.startswith("sqlite"):
    db_path = Path("data")
    db_path.mkdir(exist_ok=True)
