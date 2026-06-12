"""Application configuration using pydantic-settings.

Loads settings from environment variables with .env file fallback.
All configuration is centralized here — no hardcoded values elsewhere.

Environment variables take precedence over .env file values.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All fields are loaded from the environment.  The .env file in the
    backend directory is used as a fallback during local development.

    Never instantiate this class directly — use ``get_settings()`` which
    returns a cached singleton.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    APP_NAME: str = "StaySync"
    APP_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # ── Database ─────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/staysync"
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # ── Authentication ───────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Redis ────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── CORS ─────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ── Email (Phase 2) ──────────────────────────────────────
    EMAIL_PROVIDER: str = "resend"
    EMAIL_API_KEY: str = ""
    EMAIL_FROM_ADDRESS: str = "noreply@staysync.app"

    # ── Google Maps ──────────────────────────────────────────
    GOOGLE_MAPS_API_KEY: str = ""

    # ── Rate Limiting ────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 100

    # ── Supabase Storage (Phase 1.5) ─────────────────────────
    SUPABASE_STORAGE_BUCKET: str = "property-images"
    MAX_IMAGE_SIZE_BYTES: int = 5_242_880  # 5 MB
    ALLOWED_IMAGE_MIMES: str = "image/jpeg,image/png,image/webp"

    # ── Computed properties ───────────────────────────────────

    @property
    def is_development(self) -> bool:
        """Return True when running in the development environment."""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """Return True when running in the production environment."""
        return self.ENVIRONMENT == "production"

    @property
    def is_staging(self) -> bool:
        """Return True when running in the staging environment."""
        return self.ENVIRONMENT == "staging"

    @property
    def cors_origins(self) -> list[str]:
        """Parsed list of allowed CORS origins."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    # ── Validators ────────────────────────────────────────────

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure LOG_LEVEL is a valid Python logging level name."""
        import logging

        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}, got {v!r}")
        return upper

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        """Warn when insecure defaults are used in production/staging."""
        import warnings

        if self.ENVIRONMENT != "development":
            if self.JWT_SECRET_KEY == "change-me-in-production":
                warnings.warn(
                    "JWT_SECRET_KEY is using the insecure default value in "
                    f"{self.ENVIRONMENT} environment. Set a strong secret.",
                    stacklevel=2,
                )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings singleton.

    The instance is created once and cached for the lifetime of the process.
    To clear the cache in tests, call ``get_settings.cache_clear()``.
    """
    return Settings()
