"""Amenity repository — data access for the ``amenities`` table."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.amenity import Amenity


class AmenityRepository:
    """Data access layer for the ``amenities`` master catalog.

    Does not extend BaseRepository because Amenity does not inherit
    from TimestampedBase (no deleted_at column).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Amenity]:
        """Fetch all amenities ordered by category then name."""
        stmt = select(Amenity).order_by(Amenity.category, Amenity.name)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get(self, amenity_id: uuid.UUID) -> Amenity | None:
        """Fetch a single amenity by ID."""
        stmt = select(Amenity).where(Amenity.id == amenity_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_ids(self, amenity_ids: list[uuid.UUID]) -> list[Amenity]:
        """Fetch multiple amenities by their IDs for validation.

        Args:
            amenity_ids: List of UUIDs to fetch.

        Returns:
            List of found Amenity instances (may be fewer than input).
        """
        if not amenity_ids:
            return []
        stmt = select(Amenity).where(Amenity.id.in_(amenity_ids))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
