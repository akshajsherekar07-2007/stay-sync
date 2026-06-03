"""Pagination dependency for list endpoints.

Provides a reusable ``PaginationParams`` FastAPI dependency that extracts
and validates ``page`` and ``page_size`` query parameters from the request.

Usage
-----
.. code-block:: python

    from app.dependencies.pagination import PaginationParams
    from fastapi import Depends

    @router.get("/properties")
    async def list_properties(
        pagination: PaginationParams = Depends(),
    ) -> ...:
        offset = pagination.offset
        limit  = pagination.page_size
        ...

Limits are enforced by constants:
  - Minimum page size: 1
  - Maximum page size: ``MAX_PAGE_SIZE`` (100 per PROJECT_RULES.md)
  - Default page size: ``DEFAULT_PAGE_SIZE`` (20)
"""

from __future__ import annotations

from fastapi import Query

from app.core.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class PaginationParams:
    """Query-parameter based pagination.

    FastAPI will automatically inject this class when used as a dependency.

    Attributes
    ----------
    page      : Current page number (1-indexed, minimum 1).
    page_size : Items per page (1–MAX_PAGE_SIZE, default DEFAULT_PAGE_SIZE).
    offset    : Computed SQL offset (``(page - 1) * page_size``).
    """

    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Page number (1-indexed)."),
        page_size: int = Query(
            default=DEFAULT_PAGE_SIZE,
            ge=1,
            le=MAX_PAGE_SIZE,
            description=f"Items per page (1–{MAX_PAGE_SIZE}).",
        ),
    ) -> None:
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        """SQL OFFSET value for this page."""
        return (self.page - 1) * self.page_size
