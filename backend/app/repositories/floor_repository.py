"""Floor repository — data access for the ``floors`` table."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.floor import Floor
from app.models.room import Room
from app.repositories.base import BaseRepository


class FloorRepository(BaseRepository[Floor]):
    """Data access layer for the ``floors`` table."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Floor)

    async def list_by_property(self, property_id: uuid.UUID) -> list[Floor]:
        """Fetch all non-deleted floors for a property, ordered by sort_order.

        Args:
            property_id: The property UUID.

        Returns:
            List of Floor instances.
        """
        stmt = (
            select(Floor)
            .where(Floor.property_id == property_id)
            .where(Floor.deleted_at.is_(None))
            .order_by(Floor.sort_order)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_rooms(self, floor_id: uuid.UUID) -> Floor | None:
        """Fetch a floor with eager-loaded rooms and beds.

        Args:
            floor_id: The floor UUID.

        Returns:
            Floor with rooms loaded, or None.
        """
        stmt = (
            select(Floor)
            .options(
                selectinload(Floor.rooms).selectinload(Room.beds),
            )
            .where(Floor.id == floor_id)
            .where(Floor.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
