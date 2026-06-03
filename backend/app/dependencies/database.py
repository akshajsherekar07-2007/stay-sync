"""Database dependency provider.

Re-exports ``get_db`` from ``app.db.session`` as the canonical FastAPI
dependency for injecting an ``AsyncSession`` into route handlers.

Usage
-----
.. code-block:: python

    from app.dependencies.database import get_db
    from sqlalchemy.ext.asyncio import AsyncSession

    @router.get("/example")
    async def example(db: AsyncSession = Depends(get_db)) -> ...:
        result = await db.execute(...)
        ...

The session is committed/rolled back by the caller.  The dependency
generator handles rollback on exception and always closes the session.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db as _get_db


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session.

    This is the canonical FastAPI dependency for database access.
    Import from here (not directly from ``app.db.session``) to keep
    the dependency injection layer as the single point of use in routes.
    """
    async for session in _get_db():
        yield session
