"""WaitlistEntry repository — data access for the ``waitlist_entries`` table.

Extends ``BaseRepository[WaitlistEntry]`` with FIFO queue management
queries, position calculation, and promotion helpers.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import WaitlistStatus
from app.models.waitlist_entry import WaitlistEntry
from app.repositories.base import BaseRepository


class WaitlistEntryRepository(BaseRepository[WaitlistEntry]):
    """Data access layer for the ``waitlist_entries`` table."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, WaitlistEntry)

    # ── Position helpers ─────────────────────────────────────────────────────

    async def next_position(self, bed_id: uuid.UUID) -> int:
        """Calculate the next queue position for a bed's waitlist.

        Returns:
            The next position number (max existing + 1, or 1 if empty).
        """
        stmt = (
            select(func.coalesce(func.max(WaitlistEntry.position), 0))
            .where(WaitlistEntry.bed_id == bed_id)
            .where(WaitlistEntry.status == WaitlistStatus.ACTIVE.value)
            .where(WaitlistEntry.deleted_at.is_(None))
        )
        max_pos = (await self._session.execute(stmt)).scalar() or 0
        return max_pos + 1

    async def get_next_in_queue(
        self, bed_id: uuid.UUID
    ) -> WaitlistEntry | None:
        """Fetch the active entry with the lowest position for a bed.

        This is the student who should be promoted when the current
        hold expires or is cancelled.
        """
        stmt = (
            select(WaitlistEntry)
            .where(WaitlistEntry.bed_id == bed_id)
            .where(WaitlistEntry.status == WaitlistStatus.ACTIVE.value)
            .where(WaitlistEntry.deleted_at.is_(None))
            .order_by(WaitlistEntry.position.asc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # ── Existence checks ─────────────────────────────────────────────────────

    async def is_student_in_queue(
        self, bed_id: uuid.UUID, student_id: uuid.UUID
    ) -> bool:
        """Check if a student already has an active waitlist entry for a bed."""
        stmt = (
            select(func.count())
            .select_from(WaitlistEntry)
            .where(WaitlistEntry.bed_id == bed_id)
            .where(WaitlistEntry.student_id == student_id)
            .where(WaitlistEntry.status == WaitlistStatus.ACTIVE.value)
            .where(WaitlistEntry.deleted_at.is_(None))
        )
        count = (await self._session.execute(stmt)).scalar() or 0
        return count > 0

    async def count_active_for_bed(self, bed_id: uuid.UUID) -> int:
        """Count active waitlist entries for a bed."""
        stmt = (
            select(func.count())
            .select_from(WaitlistEntry)
            .where(WaitlistEntry.bed_id == bed_id)
            .where(WaitlistEntry.status == WaitlistStatus.ACTIVE.value)
            .where(WaitlistEntry.deleted_at.is_(None))
        )
        return (await self._session.execute(stmt)).scalar() or 0

    # ── List queries ─────────────────────────────────────────────────────────

    async def list_active_for_bed(
        self, bed_id: uuid.UUID
    ) -> list[WaitlistEntry]:
        """All active waitlist entries for a bed, ordered by position."""
        stmt = (
            select(WaitlistEntry)
            .where(WaitlistEntry.bed_id == bed_id)
            .where(WaitlistEntry.status == WaitlistStatus.ACTIVE.value)
            .where(WaitlistEntry.deleted_at.is_(None))
            .order_by(WaitlistEntry.position.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_student(
        self,
        student_id: uuid.UUID,
        status: WaitlistStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[WaitlistEntry], int]:
        """Paginated waitlist entries for a student, optionally filtered.

        Returns:
            Tuple of (items, total_count).
        """
        base = (
            select(WaitlistEntry)
            .where(WaitlistEntry.student_id == student_id)
            .where(WaitlistEntry.deleted_at.is_(None))
        )
        if status is not None:
            base = base.where(WaitlistEntry.status == status.value)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            base.order_by(WaitlistEntry.joined_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def list_by_property(
        self,
        property_id: uuid.UUID,
        status: WaitlistStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[WaitlistEntry], int]:
        """Paginated waitlist entries for a property (owner view).

        Returns:
            Tuple of (items, total_count).
        """
        base = (
            select(WaitlistEntry)
            .where(WaitlistEntry.property_id == property_id)
            .where(WaitlistEntry.deleted_at.is_(None))
        )
        if status is not None:
            base = base.where(WaitlistEntry.status == status.value)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            base.order_by(WaitlistEntry.joined_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    # ── Status transition ────────────────────────────────────────────────────

    async def promote(self, entry_id: uuid.UUID) -> WaitlistEntry | None:
        """Transition a waitlist entry to PROMOTED status.

        Sets ``promoted_at`` to the current UTC time.

        Returns the updated record, or ``None`` if not found.
        """
        now = datetime.now(tz=timezone.utc)
        stmt = (
            update(WaitlistEntry)
            .where(WaitlistEntry.id == entry_id)
            .where(WaitlistEntry.status == WaitlistStatus.ACTIVE.value)
            .where(WaitlistEntry.deleted_at.is_(None))
            .values(
                status=WaitlistStatus.PROMOTED.value,
                promoted_at=now,
            )
            .returning(WaitlistEntry)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def cancel(self, entry_id: uuid.UUID) -> WaitlistEntry | None:
        """Transition a waitlist entry to CANCELLED status.

        Sets ``cancelled_at`` to the current UTC time.

        Returns the updated record, or ``None`` if not found.
        """
        now = datetime.now(tz=timezone.utc)
        stmt = (
            update(WaitlistEntry)
            .where(WaitlistEntry.id == entry_id)
            .where(WaitlistEntry.status == WaitlistStatus.ACTIVE.value)
            .where(WaitlistEntry.deleted_at.is_(None))
            .values(
                status=WaitlistStatus.CANCELLED.value,
                cancelled_at=now,
            )
            .returning(WaitlistEntry)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def cancel_all_for_bed(self, bed_id: uuid.UUID) -> int:
        """Cancel all active waitlist entries for a bed.

        Used when a bed is directly booked or removed.
        Returns the number of rows cancelled.
        """
        now = datetime.now(tz=timezone.utc)
        stmt = (
            update(WaitlistEntry)
            .where(WaitlistEntry.bed_id == bed_id)
            .where(WaitlistEntry.status == WaitlistStatus.ACTIVE.value)
            .where(WaitlistEntry.deleted_at.is_(None))
            .values(
                status=WaitlistStatus.CANCELLED.value,
                cancelled_at=now,
            )
        )
        result = await self._session.execute(stmt)
        return result.rowcount

    async def reposition_after_removal(
        self, bed_id: uuid.UUID, removed_position: int
    ) -> int:
        """Decrement position by 1 for all active entries above the removed position.

        Called after a student is promoted or cancels to close the gap.
        Returns the number of rows updated.
        """
        stmt = (
            update(WaitlistEntry)
            .where(WaitlistEntry.bed_id == bed_id)
            .where(WaitlistEntry.status == WaitlistStatus.ACTIVE.value)
            .where(WaitlistEntry.position > removed_position)
            .where(WaitlistEntry.deleted_at.is_(None))
            .values(position=WaitlistEntry.position - 1)
        )
        result = await self._session.execute(stmt)
        return result.rowcount
