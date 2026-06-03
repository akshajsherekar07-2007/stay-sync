"""Health check endpoints.

Implements the three standard health check endpoints required by Phase 1.3:

  GET /health        — Full health check with component status
  GET /health/live   — Kubernetes-style liveness probe (always 200 if process is up)
  GET /health/ready  — Kubernetes-style readiness probe (checks DB connectivity)

All endpoints return the ``HealthResponse`` schema.

Probe semantics
---------------
``/health/live``
    Answers: "Is the process alive?"
    Returns 200 as long as the FastAPI event loop is responding.
    Does NOT check external dependencies.

``/health/ready``
    Answers: "Is the service ready to accept traffic?"
    Checks: database connectivity.
    Returns 200 only if all checked components are healthy.
    Returns 503 if any required component is unhealthy.

``/health``
    Full diagnostic check — same as ready but includes all component details.
    Returns 200 (healthy), 207 (degraded), or 503 (unhealthy).
"""

from __future__ import annotations

import time

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import get_engine
from app.schemas.common import ComponentHealth, HealthResponse

logger = get_logger(__name__)

health_router = APIRouter(prefix="/health", tags=["Health"])

settings = get_settings()


async def _check_database() -> ComponentHealth:
    """Perform a lightweight database connectivity check.

    Executes ``SELECT 1`` against the configured async engine.
    Measures round-trip latency and returns a ``ComponentHealth`` result.
    """
    start = time.perf_counter()
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return ComponentHealth(status="healthy", latency_ms=latency_ms)
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.warning("health_check_db_failed", error=str(exc))
        return ComponentHealth(
            status="unhealthy",
            latency_ms=latency_ms,
            details=str(exc),
        )


@health_router.get(
    "/live",
    summary="Liveness probe",
    description=(
        "Lightweight liveness check — returns 200 if the process is running. "
        "Does not check external dependencies. Suitable for Kubernetes/Render liveness probes."
    ),
    response_model=HealthResponse,
    responses={200: {"description": "Process is alive"}},
)
async def liveness() -> HealthResponse:
    """Always returns 200 while the event loop is running."""
    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        components={},
    )


@health_router.get(
    "/ready",
    summary="Readiness probe",
    description=(
        "Readiness check — verifies database connectivity before accepting traffic. "
        "Returns 200 if ready, 503 if any required dependency is unhealthy."
    ),
    response_model=HealthResponse,
    responses={
        200: {"description": "Service is ready to accept requests"},
        503: {"description": "Service is not ready — one or more dependencies unhealthy"},
    },
)
async def readiness() -> JSONResponse:
    """Check database connectivity. Returns 503 if DB is unreachable."""
    db_health = await _check_database()

    overall = "healthy" if db_health.status == "healthy" else "unhealthy"
    status_code = 200 if overall == "healthy" else 503

    response = HealthResponse(
        status=overall,
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        components={"database": db_health},
    )

    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(),
    )


@health_router.get(
    "",
    summary="Full health check",
    description=(
        "Comprehensive health report including all system components. "
        "Returns 200 (healthy), 207 (degraded), or 503 (unhealthy)."
    ),
    response_model=HealthResponse,
    responses={
        200: {"description": "All components healthy"},
        207: {"description": "Service degraded — some non-critical components unhealthy"},
        503: {"description": "Service unhealthy — critical components unavailable"},
    },
)
async def full_health() -> JSONResponse:
    """Full diagnostic health check with per-component breakdown."""
    db_health = await _check_database()

    components: dict[str, ComponentHealth] = {
        "database": db_health,
    }

    # Determine aggregate status
    statuses = {c.status for c in components.values()}
    if "unhealthy" in statuses:
        overall = "unhealthy"
        status_code = 503
    elif "degraded" in statuses:
        overall = "degraded"
        status_code = 207
    else:
        overall = "healthy"
        status_code = 200

    response = HealthResponse(
        status=overall,
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        components=components,
    )

    logger.info(
        "health_check",
        overall=overall,
        components={k: v.status for k, v in components.items()},
    )

    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(),
    )
