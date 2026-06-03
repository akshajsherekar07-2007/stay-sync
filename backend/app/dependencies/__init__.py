"""FastAPI dependency injection package.

Re-exports all injectable dependencies for convenient import in route handlers.

Usage
-----
.. code-block:: python

    from app.dependencies import get_db, PaginationParams
    from fastapi import Depends
    from sqlalchemy.ext.asyncio import AsyncSession

    @router.get("/items")
    async def list_items(
        db: AsyncSession = Depends(get_db),
        pagination: PaginationParams = Depends(),
    ) -> ...:
        ...
"""

from app.dependencies.database import get_db
from app.dependencies.pagination import PaginationParams

__all__ = [
    "PaginationParams",
    "get_db",
]
