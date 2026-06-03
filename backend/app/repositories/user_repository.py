"""User repository — data access for the ``users`` table.

Extends ``BaseRepository[User]`` with auth-specific query methods.
All database queries for users go through this class.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data access layer for the ``users`` table.

    Args:
        session: Active async SQLAlchemy session.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a non-deleted user by email address (case-sensitive).

        Args:
            email: The email address to look up.

        Returns:
            The matching ``User`` or ``None``.
        """
        stmt = (
            select(User)
            .where(User.email == email)
            .where(User.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_profile(self, user_id: uuid.UUID) -> User | None:
        """Fetch a user with the related profile loaded in one query.

        Uses ``selectinload`` to avoid N+1 issues.

        Args:
            user_id: The user UUID.

        Returns:
            ``User`` with ``.profile`` populated, or ``None``.
        """
        stmt = (
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == user_id)
            .where(User.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_last_login(self, user_id: uuid.UUID) -> None:
        """Update the ``last_login_at`` timestamp to now.

        Args:
            user_id: The user UUID.
        """
        from datetime import datetime, timezone

        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(last_login_at=datetime.now(tz=timezone.utc))
        )
        await self._session.execute(stmt)
