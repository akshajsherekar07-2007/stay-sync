"""Room repository — data access for the ``rooms`` table."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.bed import Bed
from app.models.room import Room
from app.repositories.base import BaseRepository


class RoomRepository(BaseRepository[Room]):
    """Data access layer for the ``rooms`` table."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Room)

    async def list_by_floor(self, floor_id: uuid.UUID) -> list[Room]:
        """Fetch all non-deleted rooms for a floor, ordered by sort_order."""
        stmt = (
            select(Room)
            .where(Room.floor_id == floor_id)
            .where(Room.deleted_at.is_(None))
            .order_by(Room.sort_order)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_beds(self, room_id: uuid.UUID) -> Room | None:
        """Fetch a room with eager-loaded beds."""
        stmt = (
            select(Room)
            .options(selectinload(Room.beds))
            .where(Room.id == room_id)
            .where(Room.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
