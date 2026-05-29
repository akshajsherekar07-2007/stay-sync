"""StaySync FastAPI Application Factory.

Creates and configures the FastAPI application instance
with middleware, routers, and event handlers.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager for startup/shutdown events."""
    settings = get_settings()
    # ── Startup ──────────────────────────────────────────────
    if settings.is_development:
        print(f"🚀 {settings.APP_NAME} starting in {settings.ENVIRONMENT} mode")
    yield
    # ── Shutdown ─────────────────────────────────────────────
    if settings.is_development:
        print(f"🛑 {settings.APP_NAME} shutting down")


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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ──────────────────────────────────────────────
    from app.api.v1.router import api_v1_router

    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    # ── Health Check ─────────────────────────────────────────
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        return {"status": "healthy", "service": settings.APP_NAME}

    return app


app = create_app()
