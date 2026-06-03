"""Request-ID middleware.

Injects a unique UUID4 ``X-Request-ID`` header into every request/response
and binds it to the structlog context so all log events within that request
automatically include the ``request_id`` field.

This middleware must be registered FIRST (outermost) in the middleware stack
so that the request ID is available to all downstream middleware and handlers.

Usage
-----
In application factory:

.. code-block:: python

    app.add_middleware(RequestIdMiddleware)

Downstream handlers can retrieve the request ID:

.. code-block:: python

    from app.middleware.request_id import get_request_id
    request_id = get_request_id(request)
"""

from __future__ import annotations

import uuid
from collections.abc import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

REQUEST_ID_HEADER = "X-Request-ID"
_REQUEST_ID_STATE_KEY = "request_id"


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Generates and propagates a unique request ID for every HTTP request.

    Priority:
        1. Uses the ``X-Request-ID`` header from the incoming request if present.
        2. Generates a new UUID4 if the header is absent.

    The ID is:
        - Stored in ``request.state.request_id``
        - Bound to the structlog context (clears on request end)
        - Set on the outgoing response as ``X-Request-ID``
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:  # type: ignore[type-arg]
        # Honour client-provided request ID or generate a fresh one
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())

        # Store on request state — accessible via get_request_id(request)
        request.state.request_id = request_id

        # Bind to structlog context vars — cleared automatically after request
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        response: Response = await call_next(request)

        # Echo the request ID back in the response header
        response.headers[REQUEST_ID_HEADER] = request_id

        return response


def get_request_id(request: Request) -> str:
    """Extract the request ID from the request state.

    Falls back to an empty string if middleware was not applied
    (e.g., during testing without full middleware stack).

    Args:
        request: The FastAPI/Starlette request object.

    Returns:
        UUID4 string or empty string.
    """
    return getattr(request.state, _REQUEST_ID_STATE_KEY, "")
