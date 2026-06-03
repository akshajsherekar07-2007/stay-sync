"""Generic async CRUD base repository.

All feature-specific repositories extend ``BaseRepository[T]``.
It provides create, get, update, soft-delete, and list operations
that work with any ``TimestampedBase`` subclass.

Usage
-----
.. code-block:: python

    class UserRepository(BaseRepository[User]):
        pass

    repo = UserRepository(db_session)
    user = await repo.get(user_id)
"""

from __future__ import annotations

import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import TimestampedBase

ModelT = TypeVar("ModelT", bound=TimestampedBase)


class BaseRepository(Generic[ModelT]):
    """Generic async CRUD repository.

    Args:
        session: An active SQLAlchemy async session (injected via Depends).
        model:   The SQLAlchemy model class this repository manages.
    """

    def __init__(self, session: AsyncSession, model: type[ModelT]) -> None:
        self._session = session
        self._model = model

    # ── Core CRUD ─────────────────────────────────────────────────────────────

    async def get(self, record_id: uuid.UUID) -> ModelT | None:
        """Fetch a single non-deleted record by primary key.

        Args:
            record_id: The UUID primary key.

        Returns:
            The model instance or ``None`` if not found / soft-deleted.
        """
        stmt = (
            select(self._model)
            .where(self._model.id == record_id)
            .where(self._model.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, **kwargs: Any) -> ModelT:
        """Create and persist a new record.

        Args:
            **kwargs: Column values for the new record.

        Returns:
            The newly created and refreshed model instance.
        """
        instance = self._model(**kwargs)
        self._session.add(instance)
        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    async def update(self, record_id: uuid.UUID, **kwargs: Any) -> ModelT | None:
        """Update specific columns on an existing record.

        Args:
            record_id: The UUID primary key.
            **kwargs:  Column-value pairs to update.

        Returns:
            The updated model instance, or ``None`` if not found.
        """
        stmt = (
            update(self._model)
            .where(self._model.id == record_id)
            .where(self._model.deleted_at.is_(None))
            .values(**kwargs)
            .returning(self._model)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def soft_delete(self, record_id: uuid.UUID) -> bool:
        """Soft-delete a record by setting its ``deleted_at`` timestamp.

        Args:
            record_id: The UUID primary key.

        Returns:
            ``True`` if a record was found and deleted, ``False`` otherwise.
        """
        from datetime import datetime, timezone

        stmt = (
            update(self._model)
            .where(self._model.id == record_id)
            .where(self._model.deleted_at.is_(None))
            .values(deleted_at=datetime.now(tz=timezone.utc))
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0
