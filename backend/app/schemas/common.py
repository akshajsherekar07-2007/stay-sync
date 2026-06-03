"""Standard API response schemas for StaySync.

Every endpoint MUST return one of these Pydantic response models so that
the API surface is predictable and self-documenting.

Response envelope design
------------------------
All responses share a top-level structure:

  {
    "success": true | false,
    "data":    <T> | null,
    "error":   null | { "code": "...", "message": "...", "details": {} },
    "meta":    { "request_id": "...", ... }
  }

Generic types
-------------
``SuccessResponse[T]``     — single-object success response
``PaginatedResponse[T]``   — paginated list with cursor/total info
``ErrorResponse``          — error body (returned by exception handlers)
``MessageResponse``        — simple { "message": "..." } response for actions
``HealthResponse``         — health-check endpoint response
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ── Shared meta block ─────────────────────────────────────────────────────────


class ResponseMeta(BaseModel):
    """Metadata attached to every API response.

    Attributes
    ----------
    request_id : Unique ID for this HTTP request (UUID4 injected by middleware).
    api_version: Always ``"v1"`` in Phase 1.
    """

    request_id: str = Field(
        ...,
        description="UUID4 identifier for this specific request, injected by middleware.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    api_version: str = Field(
        default="v1",
        description="API version that served this response.",
    )


# ── Success responses ─────────────────────────────────────────────────────────


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response wrapping a single data object.

    Usage
    -----
    .. code-block:: python

        @router.get("/users/{user_id}", response_model=SuccessResponse[UserRead])
        async def get_user(user_id: uuid.UUID) -> SuccessResponse[UserRead]:
            user = await user_service.get(user_id)
            return SuccessResponse(data=user, meta=build_meta(request))
    """

    success: bool = Field(default=True, description="Always True for success responses.")
    data: T = Field(..., description="The response payload.")
    error: None = Field(default=None, description="Always null for success responses.")
    meta: ResponseMeta = Field(..., description="Request metadata.")


class MessageResponse(BaseModel):
    """Simple confirmation response for actions that have no meaningful return value.

    Examples: logout, delete, send-email confirmation.
    """

    success: bool = Field(default=True)
    message: str = Field(..., description="Human-readable confirmation message.")
    error: None = Field(default=None)
    meta: ResponseMeta = Field(..., description="Request metadata.")


# ── Pagination ────────────────────────────────────────────────────────────────


class PaginationInfo(BaseModel):
    """Pagination metadata attached to list responses."""

    page: int = Field(..., ge=1, description="Current page number (1-indexed).")
    page_size: int = Field(..., ge=1, description="Number of items per page.")
    total_items: int = Field(..., ge=0, description="Total number of matching items.")
    total_pages: int = Field(..., ge=0, description="Total number of pages.")
    has_next: bool = Field(..., description="True if a next page exists.")
    has_prev: bool = Field(..., description="True if a previous page exists.")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated list response.

    Usage
    -----
    .. code-block:: python

        @router.get("/properties", response_model=PaginatedResponse[PropertyRead])
        async def list_properties(...) -> PaginatedResponse[PropertyRead]:
            items, total = await property_service.list(page=page, page_size=page_size)
            return PaginatedResponse(
                data=items,
                pagination=PaginationInfo(...),
                meta=build_meta(request),
            )
    """

    success: bool = Field(default=True)
    data: list[T] = Field(..., description="The list of items for the current page.")
    pagination: PaginationInfo = Field(..., description="Pagination metadata.")
    error: None = Field(default=None)
    meta: ResponseMeta = Field(..., description="Request metadata.")


# ── Error responses ───────────────────────────────────────────────────────────


class ErrorDetail(BaseModel):
    """Structured error information returned when ``success`` is False."""

    code: str = Field(
        ...,
        description="Machine-readable error code (UPPER_SNAKE_CASE).",
        examples=["NOT_FOUND", "RATE_LIMITED", "VALIDATION_ERROR"],
    )
    message: str = Field(
        ...,
        description="Human-readable description of the error.",
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional structured context — field errors, limits, etc.",
    )


class ErrorResponse(BaseModel):
    """Standard error response envelope.

    Returned by all exception handlers.  Always has ``success: false``.
    """

    success: bool = Field(default=False)
    data: None = Field(default=None, description="Always null for error responses.")
    error: ErrorDetail = Field(..., description="Structured error information.")
    meta: ResponseMeta = Field(..., description="Request metadata.")


# ── Health check response ─────────────────────────────────────────────────────


class ComponentHealth(BaseModel):
    """Health status of a single system component."""

    status: str = Field(
        ...,
        description="One of: ``healthy``, ``degraded``, ``unhealthy``.",
        examples=["healthy"],
    )
    latency_ms: float | None = Field(
        default=None,
        description="Round-trip latency in milliseconds (if measurable).",
    )
    details: str | None = Field(
        default=None,
        description="Optional human-readable explanation (e.g., error message).",
    )


class HealthResponse(BaseModel):
    """Response schema for health-check endpoints."""

    status: str = Field(
        ...,
        description="Aggregate status: ``healthy``, ``degraded``, or ``unhealthy``.",
        examples=["healthy"],
    )
    service: str = Field(..., description="Service name.", examples=["StaySync"])
    version: str = Field(..., description="Application version string.")
    environment: str = Field(
        ...,
        description="Runtime environment name.",
        examples=["production"],
    )
    components: dict[str, ComponentHealth] = Field(
        default_factory=dict,
        description="Per-component health breakdown.",
    )


# ── Helper factory ────────────────────────────────────────────────────────────


def build_meta(request_id: str) -> ResponseMeta:
    """Construct a ``ResponseMeta`` instance.

    Args:
        request_id: The UUID string injected by ``RequestIdMiddleware``.

    Returns:
        ``ResponseMeta`` ready to embed in any response model.
    """
    return ResponseMeta(request_id=request_id)
