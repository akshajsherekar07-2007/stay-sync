"""Bed repository — data access for the ``beds`` table."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bed import Bed
from app.repositories.base import BaseRepository


class BedRepository(BaseRepository[Bed]):
    """Data access layer for the ``beds`` table."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Bed)

    async def list_by_room(self, room_id: uuid.UUID) -> list[Bed]:
        """Fetch all non-deleted beds for a room, ordered by sort_order."""
        stmt = (
            select(Bed)
            .where(Bed.room_id == room_id)
            .where(Bed.deleted_at.is_(None))
            .order_by(Bed.sort_order)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_property(self, property_id: uuid.UUID) -> list[Bed]:
        """Fetch all non-deleted beds for a property."""
        stmt = (
            select(Bed)
            .where(Bed.property_id == property_id)
            .where(Bed.deleted_at.is_(None))
            .order_by(Bed.sort_order)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
