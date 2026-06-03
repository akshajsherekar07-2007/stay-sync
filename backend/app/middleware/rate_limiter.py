"""In-process sliding-window rate limiter middleware.

Uses an in-memory fixed-window counter keyed by client IP.  This
implementation is suitable for single-process deployments (e.g., a single
Render web service instance).  For multi-process / multi-instance deployments,
replace this with a Redis-backed implementation in Phase 2.

Configuration
-------------
Controlled via the ``RATE_LIMIT_PER_MINUTE`` environment variable (default 100).

Client identification
---------------------
The limiter identifies clients by IP address, using the ``X-Forwarded-For``
header when behind a reverse proxy (Render, nginx, Cloudflare).

Exempt paths
------------
Health check endpoints are exempt to allow load-balancer liveness probes.

Response
--------
When the limit is exceeded, returns HTTP 429 with the standard error envelope
and a ``Retry-After`` header indicating when the window resets.
"""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Paths that bypass rate limiting (load balancer health probes etc.)
_EXEMPT_PATHS: frozenset[str] = frozenset(
    {
        "/health",
        "/health/live",
        "/health/ready",
    }
)


class _WindowCounter:
    """Fixed-window counter for a single client."""

    __slots__ = ("count", "window_start")

    def __init__(self) -> None:
        self.count: int = 0
        self.window_start: float = time.monotonic()


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """In-process fixed-window rate limiter.

    Thread safety: ``defaultdict`` operations in CPython are GIL-protected,
    which is sufficient for async request handling with a single event loop.
    """

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        self._counters: defaultdict[str, _WindowCounter] = defaultdict(_WindowCounter)
        self._window_seconds: float = 60.0
        self._limit: int = get_settings().RATE_LIMIT_PER_MINUTE

    def _get_client_key(self, request: Request) -> str:
        """Resolve the client identifier (IP address) from the request."""
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _check_rate_limit(self, client_key: str) -> tuple[bool, float, int]:
        """Check and update the rate limit counter for a client.

        Returns:
            Tuple of (is_allowed, retry_after_seconds, remaining_requests).
        """
        now = time.monotonic()
        counter = self._counters[client_key]

        # Reset counter if window has expired
        if now - counter.window_start >= self._window_seconds:
            counter.count = 0
            counter.window_start = now

        counter.count += 1

        if counter.count > self._limit:
            retry_after = self._window_seconds - (now - counter.window_start)
            return False, retry_after, 0

        remaining = max(0, self._limit - counter.count)
        return True, 0.0, remaining

    async def dispatch(self, request: Request, call_next: Callable) -> Response:  # type: ignore[type-arg]
        if request.url.path in _EXEMPT_PATHS:
            return await call_next(request)  # type: ignore[return-value]

        client_key = self._get_client_key(request)
        allowed, retry_after, remaining = self._check_rate_limit(client_key)

        if not allowed:
            logger.warning(
                "rate_limit_exceeded",
                client_ip=client_key,
                path=request.url.path,
                limit=self._limit,
            )
            request_id = getattr(request.state, "request_id", "")
            return JSONResponse(
                status_code=429,
                headers={
                    "Retry-After": str(int(retry_after)),
                    "X-RateLimit-Limit": str(self._limit),
                    "X-RateLimit-Remaining": "0",
                    "X-Request-ID": request_id,
                },
                content={
                    "success": False,
                    "data": None,
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": "Rate limit exceeded. Please try again later.",
                        "details": {
                            "limit": self._limit,
                            "window_seconds": int(self._window_seconds),
                            "retry_after_seconds": int(retry_after),
                        },
                    },
                    "meta": {"request_id": request_id, "api_version": "v1"},
                },
            )

        response: Response = await call_next(request)

        # Add rate-limit headers to successful responses
        response.headers["X-RateLimit-Limit"] = str(self._limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response
