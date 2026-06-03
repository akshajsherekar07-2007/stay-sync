"""Custom exception classes for StaySync.

Centralized exception hierarchy that maps cleanly to HTTP status codes.
All business-logic errors should raise one of these typed exceptions.
The global exception handler middleware catches them and returns the
standard API error envelope defined in ``schemas/common.py``.

Exception hierarchy
-------------------
StaySyncException (base)
├── BadRequestException         400
├── UnauthorizedException       401
├── ForbiddenException          403
├── NotFoundException           404
├── ConflictException           409
├── UnprocessableEntityException 422
├── RateLimitException          429
└── ServiceUnavailableException 503
"""

from __future__ import annotations

from typing import Any


class StaySyncException(Exception):
    """Base exception for all StaySync application errors.

    Args:
        message: Human-readable description shown to the API consumer.
        code: Machine-readable error code (UPPER_SNAKE_CASE).
        status_code: HTTP status code to return.
        details: Optional structured payload with additional context.
    """

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"code={self.code!r}, "
            f"status_code={self.status_code}, "
            f"message={self.message!r})"
        )


class BadRequestException(StaySyncException):
    """The request payload is syntactically invalid or logically inconsistent (400)."""

    def __init__(
        self,
        message: str = "Bad request",
        code: str = "BAD_REQUEST",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, status_code=400, details=details)


class UnauthorizedException(StaySyncException):
    """Authentication credentials are missing or invalid (401)."""

    def __init__(
        self,
        message: str = "Authentication required",
        code: str = "UNAUTHORIZED",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, status_code=401, details=details)


class ForbiddenException(StaySyncException):
    """The authenticated user lacks the required permission (403)."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        code: str = "FORBIDDEN",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, status_code=403, details=details)


class NotFoundException(StaySyncException):
    """The requested resource does not exist or is not accessible (404)."""

    def __init__(
        self,
        message: str = "Resource not found",
        code: str = "NOT_FOUND",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, status_code=404, details=details)


class ConflictException(StaySyncException):
    """The operation conflicts with the current resource state (409).

    Common use-cases: duplicate email, double-booking, optimistic lock failure.
    """

    def __init__(
        self,
        message: str = "Resource conflict",
        code: str = "CONFLICT",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, status_code=409, details=details)


class UnprocessableEntityException(StaySyncException):
    """The request is syntactically valid but semantically incorrect (422).

    Use when validation errors come from business logic rather than
    Pydantic schema validation (which is handled automatically by FastAPI).
    """

    def __init__(
        self,
        message: str = "Unprocessable entity",
        code: str = "VALIDATION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, status_code=422, details=details)


class RateLimitException(StaySyncException):
    """The client has exceeded the allowed request rate (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please try again later.",
        code: str = "RATE_LIMITED",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, status_code=429, details=details)


class ServiceUnavailableException(StaySyncException):
    """A downstream dependency (DB, Redis, external API) is unavailable (503)."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        code: str = "SERVICE_UNAVAILABLE",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, status_code=503, details=details)
