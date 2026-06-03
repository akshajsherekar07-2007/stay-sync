"""Profile repository — data access for the ``profiles`` table.

Extends ``BaseRepository[Profile]`` with profile-specific query methods.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile
from app.repositories.base import BaseRepository


class ProfileRepository(BaseRepository[Profile]):
    """Data access layer for the ``profiles`` table.

    Args:
        session: Active async SQLAlchemy session.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Profile)

    async def get_by_user_id(self, user_id: uuid.UUID) -> Profile | None:
        """Fetch the profile for a given user.

        Args:
            user_id: The owner user's UUID.

        Returns:
            The matching ``Profile`` or ``None``.
        """
        stmt = (
            select(Profile)
            .where(Profile.user_id == user_id)
            .where(Profile.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(self, user_id: uuid.UUID, **fields: Any) -> Profile:
        """Create or update a profile for the given user.

        If a profile already exists it is updated with the supplied fields.
        If it does not exist a new profile is created.

        Args:
            user_id:  The owner user's UUID.
            **fields: Column-value pairs for the profile (e.g. full_name=...).

        Returns:
            The created or updated ``Profile`` instance.
        """
        existing = await self.get_by_user_id(user_id)
        if existing is not None:
            # Partial update — only set fields that were provided
            for key, value in fields.items():
                if value is not None:
                    setattr(existing, key, value)
            await self._session.flush()
            await self._session.refresh(existing)
            return existing

        # Create a new profile
        return await self.create(user_id=user_id, **fields)

    async def update_fields(
        self,
        user_id: uuid.UUID,
        **fields: Any,
    ) -> Profile | None:
        """Partially update profile fields for a given user.

        Only non-None fields are applied (PATCH semantics).

        Args:
            user_id:  The owner user's UUID.
            **fields: Column-value pairs to update.

        Returns:
            The updated ``Profile`` or ``None`` if not found.
        """
        # Filter out None values so we only update explicitly provided fields
        updates = {k: v for k, v in fields.items() if v is not None}
        if not updates:
            return await self.get_by_user_id(user_id)

        stmt = (
            update(Profile)
            .where(Profile.user_id == user_id)
            .where(Profile.deleted_at.is_(None))
            .values(**updates)
            .returning(Profile)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
