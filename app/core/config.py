from __future__ import annotations

import functools

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_DEFAULT_KEY = "change-me-to-a-random-secret-key"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "App Starter"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "dev"  # dev | staging | prod

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/app_starter"
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # JWT
    jwt_secret_key: str = _INSECURE_DEFAULT_KEY
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440  # 24 hours

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Redis (optional, for caching)
    redis_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @model_validator(mode="after")
    def _reject_default_secret_in_prod(self) -> Settings:
        if self.environment not in ("dev", "test") and self.jwt_secret_key == _INSECURE_DEFAULT_KEY:
            raise ValueError("jwt_secret_key must be changed from the default for non-dev environments")
        return self


@functools.lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
