"""Custom exception classes for StaySync.

Centralized exceptions that map to specific HTTP status codes.
All business-logic errors should raise one of these exceptions,
which are then caught by the global exception handler middleware.
"""

from typing import Any


class StaySyncException(Exception):
    """Base exception for all StaySync application errors."""

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


class NotFoundException(StaySyncException):
    """Resource not found (404)."""

    def __init__(
        self,
        message: str = "Resource not found",
        code: str = "NOT_FOUND",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, status_code=404, details=details)


class BadRequestException(StaySyncException):
    """Invalid request data (400)."""

    def __init__(
        self,
        message: str = "Bad request",
        code: str = "BAD_REQUEST",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, status_code=400, details=details)


class UnauthorizedException(StaySyncException):
    """Authentication required (401)."""

    def __init__(
        self,
        message: str = "Authentication required",
        code: str = "UNAUTHORIZED",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, status_code=401, details=details)


class ForbiddenException(StaySyncException):
    """Insufficient permissions (403)."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        code: str = "FORBIDDEN",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, status_code=403, details=details)


class ConflictException(StaySyncException):
    """Resource conflict — double booking, race condition (409)."""

    def __init__(
        self,
        message: str = "Resource conflict",
        code: str = "CONFLICT",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, status_code=409, details=details)


class RateLimitException(StaySyncException):
    """Rate limit exceeded (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please try again later.",
        code: str = "RATE_LIMITED",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, status_code=429, details=details)
