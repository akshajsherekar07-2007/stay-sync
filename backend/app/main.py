"""StaySync FastAPI Application Factory.

Creates and configures the FastAPI application instance
with middleware, routers, and event handlers.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.init_db import init_db
from app.db.session import close_db
from app.core.redis import init_redis, close_redis
from app.websocket.manager import ConnectionManager
from app.middleware import (
    RateLimiterMiddleware,
    RequestIdMiddleware,
    RequestLoggingMiddleware,
    register_exception_handlers,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager for startup/shutdown events."""
    setup_logging()  # Structured logging must be configured before any log calls
    settings = get_settings()
    # ── Startup ──────────────────────────────────────────────
    if settings.is_development:
        print(f"[startup] {settings.APP_NAME} starting in {settings.ENVIRONMENT} mode")
    await init_db()
    await init_redis()
    # WebSocket manager stored on app.state for access from endpoints
    app.state.ws_manager = ConnectionManager()
    yield
    # ── Shutdown ─────────────────────────────────────────────
    await close_redis()
    await close_db()
    if settings.is_development:
        print(f"[shutdown] {settings.APP_NAME} shutting down")


def create_app() -> FastAPI:
    """Application factory — creates and configures the FastAPI instance."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        description="Live Accommodation Hold-Management Platform API",
        version="0.1.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # ── Middleware ────────────────────────────────────────────
    # Starlette processes add_middleware() calls in reverse order, so the last
    # call here becomes the outermost (first to receive the request).
    # Desired order (outermost → innermost):
    #   CORSMiddleware → RateLimiterMiddleware → RequestIdMiddleware → RequestLoggingMiddleware
    app.add_middleware(RequestLoggingMiddleware)  # innermost — logs after ID is bound
    app.add_middleware(RequestIdMiddleware)       # binds request ID to structlog context
    app.add_middleware(RateLimiterMiddleware)     # rate-checks before ID logging
    app.add_middleware(
        CORSMiddleware,                           # outermost — handles preflight first
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ──────────────────────────────────────────────
    from app.api.v1.health import health_router
    from app.api.v1.router import api_v1_router

    app.include_router(health_router)                               # /health, /health/live, /health/ready
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    # ── WebSocket endpoint ───────────────────────────────────
    from app.websocket.endpoint import router as ws_router
    app.include_router(ws_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_app()
