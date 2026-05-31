"""Async SQLAlchemy engine and session factory.

This module is the single source of truth for database connectivity:
  - Creates the async engine from DATABASE_URL environment variable
  - Exposes ``AsyncSessionLocal`` for use in dependency injection
  - Provides ``get_db`` async generator for FastAPI dependencies

The engine is configured conservatively with:
  - Connection pool size appropriate for Supabase's limits
  - Echo disabled in production
  - Pool pre-ping enabled to recover from stale connections
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

# ── Module-level singletons — initialised once per process ───────────────────
# These are lazily created on first access so that import-time side effects
# (e.g., reading .env) do not break unit tests that patch settings.

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_engine() -> AsyncEngine:
    """Return (or create) the module-level async engine singleton."""
    global _engine  # noqa: PLW0603 — intentional module-level singleton
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=1800,  # recycle connections every 30 minutes
        )
    return _engine


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return (or create) the module-level session factory singleton."""
    global _session_factory  # noqa: PLW0603
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=_get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _session_factory


# ── Public helpers ────────────────────────────────────────────────────────────


def get_engine() -> AsyncEngine:
    """Return the shared async engine instance."""
    return _get_engine()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a database session per request.

    Usage
    -----
    .. code-block:: python

        @router.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            ...

    The session is automatically closed (not committed) after the request.
    Callers are responsible for explicit ``await session.commit()`` calls.
    Rollback on exception is handled automatically by the context manager.
    """
    factory = _get_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def close_db() -> None:
    """Dispose the engine connection pool.

    Call during application shutdown to release all connections gracefully.
    """
    global _engine, _session_factory  # noqa: PLW0603
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
