"""FastAPI dependency injection package.

Re-exports all injectable dependencies for convenient import in route handlers.

Usage
-----
.. code-block:: python

    from app.dependencies import get_db, get_current_user, PaginationParams
    from fastapi import Depends

    @router.get("/items")
    async def list_items(
        current_user = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
        pagination: PaginationParams = Depends(),
    ) -> ...:
        ...
"""

from app.dependencies.auth import (
    get_current_user,
    get_current_user_optional,
    require_owner,
    require_role,
    require_student,
)
from app.dependencies.database import get_db
from app.dependencies.pagination import PaginationParams

__all__ = [
    # Database
    "get_db",
    # Pagination
    "PaginationParams",
    # Auth / RBAC
    "get_current_user",
    "get_current_user_optional",
    "require_owner",
    "require_role",
    "require_student",
]
