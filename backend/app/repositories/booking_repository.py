"""Booking repository — data access for the ``bookings`` table.

Extends ``BaseRepository[Booking]`` with booking-specific queries
for active-booking lookups, occupancy tracking, and status transitions.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import BookingStatus
from app.models.booking import Booking
from app.repositories.base import BaseRepository


class BookingRepository(BaseRepository[Booking]):
    """Data access layer for the ``bookings`` table."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Booking)

    # ── Single-record helpers ────────────────────────────────────────────────

    async def get_with_relations(
        self, booking_id: uuid.UUID
    ) -> Booking | None:
        """Fetch a booking with eager-loaded bed, student, property, and hold_request."""
        stmt = (
            select(Booking)
            .options(
                selectinload(Booking.bed),
                selectinload(Booking.student),
                selectinload(Booking.property),
                selectinload(Booking.hold_request),
            )
            .where(Booking.id == booking_id)
            .where(Booking.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_hold_request(
        self, hold_request_id: uuid.UUID
    ) -> Booking | None:
        """Fetch a booking created from a specific hold request."""
        stmt = (
            select(Booking)
            .where(Booking.hold_request_id == hold_request_id)
            .where(Booking.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # ── Active-booking queries ───────────────────────────────────────────────

    async def get_active_for_bed(
        self, bed_id: uuid.UUID
    ) -> Booking | None:
        """Return the single confirmed booking for a bed.

        The partial unique index ``idx_bookings_active_bed`` guarantees at
        most one confirmed booking per bed.
        """
        stmt = (
            select(Booking)
            .where(Booking.bed_id == bed_id)
            .where(Booking.status == BookingStatus.CONFIRMED.value)
            .where(Booking.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def has_active_booking(
        self, bed_id: uuid.UUID, student_id: uuid.UUID
    ) -> bool:
        """Check if a student already has a confirmed booking on a bed."""
        stmt = (
            select(func.count())
            .select_from(Booking)
            .where(Booking.bed_id == bed_id)
            .where(Booking.student_id == student_id)
            .where(Booking.status == BookingStatus.CONFIRMED.value)
            .where(Booking.deleted_at.is_(None))
        )
        count = (await self._session.execute(stmt)).scalar() or 0
        return count > 0

    async def count_active_by_student(self, student_id: uuid.UUID) -> int:
        """Count all confirmed bookings for a student across all beds."""
        stmt = (
            select(func.count())
            .select_from(Booking)
            .where(Booking.student_id == student_id)
            .where(Booking.status == BookingStatus.CONFIRMED.value)
            .where(Booking.deleted_at.is_(None))
        )
        return (await self._session.execute(stmt)).scalar() or 0

    async def count_active_by_property(self, property_id: uuid.UUID) -> int:
        """Count confirmed bookings for a property (occupancy metric)."""
        stmt = (
            select(func.count())
            .select_from(Booking)
            .where(Booking.property_id == property_id)
            .where(Booking.status == BookingStatus.CONFIRMED.value)
            .where(Booking.deleted_at.is_(None))
        )
        return (await self._session.execute(stmt)).scalar() or 0

    # ── List queries ─────────────────────────────────────────────────────────

    async def list_by_student(
        self,
        student_id: uuid.UUID,
        status: BookingStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Booking], int]:
        """Paginated bookings for a student, optionally filtered by status.

        Returns:
            Tuple of (items, total_count).
        """
        base = (
            select(Booking)
            .where(Booking.student_id == student_id)
            .where(Booking.deleted_at.is_(None))
        )
        if status is not None:
            base = base.where(Booking.status == status.value)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            base.order_by(Booking.confirmed_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def list_by_property(
        self,
        property_id: uuid.UUID,
        status: BookingStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Booking], int]:
        """Paginated bookings for a property (owner view).

        Returns:
            Tuple of (items, total_count).
        """
        base = (
            select(Booking)
            .where(Booking.property_id == property_id)
            .where(Booking.deleted_at.is_(None))
        )
        if status is not None:
            base = base.where(Booking.status == status.value)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            base.order_by(Booking.confirmed_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def list_by_bed(self, bed_id: uuid.UUID) -> list[Booking]:
        """All non-deleted bookings for a bed (any status), newest first."""
        stmt = (
            select(Booking)
            .where(Booking.bed_id == bed_id)
            .where(Booking.deleted_at.is_(None))
            .order_by(Booking.confirmed_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ── Status transition ────────────────────────────────────────────────────

    async def vacate(self, booking_id: uuid.UUID) -> Booking | None:
        """Transition a booking to VACATED status.

        Sets ``vacated_at`` to the current UTC time.

        Returns the updated record, or ``None`` if not found.
        """
        now = datetime.now(tz=timezone.utc)
        stmt = (
            update(Booking)
            .where(Booking.id == booking_id)
            .where(Booking.status == BookingStatus.CONFIRMED.value)
            .where(Booking.deleted_at.is_(None))
            .values(
                status=BookingStatus.VACATED.value,
                vacated_at=now,
            )
            .returning(Booking)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def cancel(self, booking_id: uuid.UUID) -> Booking | None:
        """Transition a booking to CANCELLED status.

        Returns the updated record, or ``None`` if not found.
        """
        stmt = (
            update(Booking)
            .where(Booking.id == booking_id)
            .where(Booking.status == BookingStatus.CONFIRMED.value)
            .where(Booking.deleted_at.is_(None))
            .values(status=BookingStatus.CANCELLED.value)
            .returning(Booking)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
