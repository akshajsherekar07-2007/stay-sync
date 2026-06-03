"""Request logging middleware.

Logs structured information about every HTTP request including:
  - HTTP method and URL path
  - Response status code
  - Wall-clock request duration (ms)
  - Request ID (from structlog context bound by RequestIdMiddleware)
  - Client IP address

All log events are structured (key=value pairs) and integrate with
the JSON output in production or the colored console in development.

Note: Health check endpoints are deliberately excluded from access logs
to reduce noise in production log streams.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)

# Paths to exclude from access log output (noisy liveness probes)
_EXCLUDED_PATHS: frozenset[str] = frozenset(
    {
        "/health",
        "/health/live",
        "/health/ready",
    }
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Structured access log entry for every non-health HTTP request.

    Log fields
    ----------
    event       : Always ``"http_request"``
    method      : HTTP verb (GET, POST, …)
    path        : URL path (query string excluded)
    status_code : Integer HTTP response status
    duration_ms : Wall-clock time in milliseconds (2 decimal places)
    client_ip   : Originating IP address (respects X-Forwarded-For)
    user_agent  : User-Agent header value (if present)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:  # type: ignore[type-arg]
        # Skip health probes — they would flood the logs
        if request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)  # type: ignore[return-value]

        start = time.perf_counter()

        response: Response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        # Resolve the real client IP (Render / nginx proxy-aware)
        client_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or (request.client.host if request.client else "unknown")
        )

        log_method = logger.info if response.status_code < 400 else logger.warning
        if response.status_code >= 500:
            log_method = logger.error

        log_method(
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client_ip=client_ip,
            user_agent=request.headers.get("User-Agent", ""),
        )

        return response
