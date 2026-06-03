"""HTTP middleware package.

Middleware is registered in the application factory (``app/main.py``) in
the following order (innermost to outermost — Starlette processes in reverse):

  1. CORSMiddleware        — outermost, handles preflight
  2. RateLimiterMiddleware — before logging, after CORS
  3. RequestIdMiddleware   — generates/propagates X-Request-ID
  4. RequestLoggingMiddleware — logs with request ID available in context

Exception handlers (not middleware) are also registered in the factory:
  - StaySyncException
  - RequestValidationError
  - HTTPException
  - Exception (catch-all)
"""

from app.middleware.error_handler import register_exception_handlers
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.middleware.request_id import RequestIdMiddleware, get_request_id
from app.middleware.request_logging import RequestLoggingMiddleware

__all__ = [
    "RateLimiterMiddleware",
    "RequestIdMiddleware",
    "RequestLoggingMiddleware",
    "get_request_id",
    "register_exception_handlers",
]
