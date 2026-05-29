"""Application configuration using pydantic-settings.

Loads settings from environment variables with .env file fallback.
All configuration is centralized here — no hardcoded values elsewhere.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "StaySync"
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

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

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings singleton."""
    return Settings()
