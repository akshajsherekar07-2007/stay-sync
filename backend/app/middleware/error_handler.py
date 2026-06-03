"""Global exception handlers for the FastAPI application.

Registers exception handlers for:
  1. ``StaySyncException`` subclasses — typed business-logic errors
  2. ``RequestValidationError`` — Pydantic 422 validation failures
  3. ``HTTPException`` — Starlette/FastAPI HTTP exceptions (e.g., 404 from routing)
  4. ``Exception`` — catch-all for unexpected server errors (500)

All handlers return the standard ``ErrorResponse`` envelope so clients always
receive a consistent JSON structure regardless of the error source.

The ``request_id`` is extracted from ``request.state`` (set by RequestIdMiddleware)
and included in every error response for correlation with server-side logs.
"""

from __future__ import annotations

import traceback

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import StaySyncException
from app.core.logging import get_logger

logger = get_logger(__name__)


def _get_request_id(request: Request) -> str:
    """Safely extract the request ID from request state."""
    return getattr(request.state, "request_id", "")


def _error_response(
    *,
    request_id: str,
    status_code: int,
    code: str,
    message: str,
    details: dict,
) -> JSONResponse:
    """Build a standard error JSONResponse."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": code,
                "message": message,
                "details": details,
            },
            "meta": {
                "request_id": request_id,
                "api_version": "v1",
            },
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all global exception handlers to the FastAPI application.

    Call this once inside ``create_app()`` after all middleware is registered.
    """

    @app.exception_handler(StaySyncException)
    async def staysync_exception_handler(
        request: Request,
        exc: StaySyncException,
    ) -> JSONResponse:
        """Handle all typed StaySync business-logic exceptions."""
        request_id = _get_request_id(request)

        # Log server errors with full context; client errors at warning level
        if exc.status_code >= 500:
            logger.error(
                "staysync_exception",
                code=exc.code,
                message=exc.message,
                status_code=exc.status_code,
                exc_info=True,
            )
        else:
            logger.warning(
                "staysync_exception",
                code=exc.code,
                message=exc.message,
                status_code=exc.status_code,
            )

        return _error_response(
            request_id=request_id,
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Handle Pydantic request-body / query-param validation errors (422).

        Transforms Pydantic's error list into a structured ``details`` dict
        so clients receive actionable field-level information.
        """
        request_id = _get_request_id(request)

        # Build a field-level error map: { "body.email": "value is not a valid email" }
        field_errors: dict[str, str] = {}
        for error in exc.errors():
            location = " → ".join(str(loc) for loc in error["loc"])
            field_errors[location] = error["msg"]

        logger.warning(
            "validation_error",
            field_count=len(field_errors),
            fields=list(field_errors.keys()),
        )

        return _error_response(
            request_id=request_id,
            status_code=422,
            code="VALIDATION_ERROR",
            message="Request validation failed. Check the details for field-level errors.",
            details={"fields": field_errors},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        """Handle FastAPI/Starlette HTTPExceptions (e.g., 404 from routing, 405 method not allowed)."""
        request_id = _get_request_id(request)

        # Map common status codes to machine-readable error codes
        _STATUS_CODE_MAP: dict[int, str] = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            408: "REQUEST_TIMEOUT",
            409: "CONFLICT",
            410: "GONE",
            413: "PAYLOAD_TOO_LARGE",
            415: "UNSUPPORTED_MEDIA_TYPE",
            422: "VALIDATION_ERROR",
            429: "RATE_LIMITED",
            500: "INTERNAL_ERROR",
            502: "BAD_GATEWAY",
            503: "SERVICE_UNAVAILABLE",
        }

        code = _STATUS_CODE_MAP.get(exc.status_code, "HTTP_ERROR")
        message = str(exc.detail) if exc.detail else "An HTTP error occurred"

        log_fn = logger.warning if exc.status_code < 500 else logger.error
        log_fn(
            "http_exception",
            status_code=exc.status_code,
            code=code,
            message=message,
        )

        return _error_response(
            request_id=request_id,
            status_code=exc.status_code,
            code=code,
            message=message,
            details={},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Catch-all handler for unexpected exceptions.

        Logs a full traceback at ERROR level and returns a generic 500 response.
        The actual error is NOT exposed to the client for security reasons.
        """
        request_id = _get_request_id(request)

        logger.error(
            "unhandled_exception",
            exc_type=type(exc).__name__,
            exc_message=str(exc),
            traceback=traceback.format_exc(),
        )

        return _error_response(
            request_id=request_id,
            status_code=500,
            code="INTERNAL_ERROR",
            message="An unexpected error occurred. Please try again later.",
            details={},
        )
