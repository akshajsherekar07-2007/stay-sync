"""Bed repository — data access for the ``beds`` table."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bed import Bed
from app.repositories.base import BaseRepository


class BedRepository(BaseRepository[Bed]):
    """Data access layer for the ``beds`` table."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Bed)

    # ── Concurrency-safe reads ───────────────────────────────────────────────

    async def get_for_update(self, bed_id: uuid.UUID) -> Bed | None:
        """Fetch a bed with a row-level ``FOR UPDATE`` lock.

        Use before any status transition to prevent concurrent modifications.
        The lock is held until the enclosing transaction commits or rolls back.

        Returns:
            The locked Bed instance, or ``None`` if not found / soft-deleted.
        """
        stmt = (
            select(Bed)
            .where(Bed.id == bed_id)
            .where(Bed.deleted_at.is_(None))
            .with_for_update()
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status_optimistic(
        self,
        bed_id: uuid.UUID,
        expected_version: int,
        *,
        status: str,
        current_hold_id: uuid.UUID | None = ...,
        current_booking_id: uuid.UUID | None = ...,
    ) -> Bed | None:
        """Atomically update bed status with optimistic lock on ``version``.

        Increments ``version`` by 1 and updates status + pointer fields.
        Returns ``None`` if the version has changed (conflict detected).

        Args:
            bed_id:              Target bed UUID.
            expected_version:    The version read by the caller.
            status:              New bed status value.
            current_hold_id:     Set to a UUID or None. Use ``...`` (sentinel)
                                 to leave unchanged.
            current_booking_id:  Set to a UUID or None. Use ``...`` (sentinel)
                                 to leave unchanged.

        Returns:
            The updated Bed if the version matched, otherwise ``None``.
        """
        values: dict[str, Any] = {
            "status": status,
            "version": expected_version + 1,
        }
        if current_hold_id is not ...:
            values["current_hold_id"] = current_hold_id
        if current_booking_id is not ...:
            values["current_booking_id"] = current_booking_id

        stmt = (
            update(Bed)
            .where(Bed.id == bed_id)
            .where(Bed.version == expected_version)
            .where(Bed.deleted_at.is_(None))
            .values(**values)
            .returning(Bed)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # ── List queries ─────────────────────────────────────────────────────────

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
