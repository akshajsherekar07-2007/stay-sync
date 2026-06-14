"""HoldRequest repository — data access for the ``hold_requests`` table.

Extends ``BaseRepository[HoldRequest]`` with domain-specific queries
for hold lifecycle management, active-hold lookups, and expiry detection.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import HoldStatus
from app.models.hold_request import HoldRequest
from app.repositories.base import BaseRepository


# Statuses considered "active" (occupy the bed slot)
_ACTIVE_STATUSES = (HoldStatus.PENDING.value, HoldStatus.APPROVED.value)

# Terminal statuses (hold is no longer actionable)
_TERMINAL_STATUSES = (
    HoldStatus.REJECTED.value,
    HoldStatus.EXPIRED.value,
    HoldStatus.OVERRIDDEN.value,
    HoldStatus.CANCELLED.value,
)


class HoldRequestRepository(BaseRepository[HoldRequest]):
    """Data access layer for the ``hold_requests`` table."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, HoldRequest)

    # ── Single-record helpers ────────────────────────────────────────────────

    async def get_with_relations(
        self, hold_id: uuid.UUID
    ) -> HoldRequest | None:
        """Fetch a hold request with eager-loaded bed, student, and property."""
        stmt = (
            select(HoldRequest)
            .options(
                selectinload(HoldRequest.bed),
                selectinload(HoldRequest.student),
                selectinload(HoldRequest.property),
            )
            .where(HoldRequest.id == hold_id)
            .where(HoldRequest.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # ── Active-hold queries ──────────────────────────────────────────────────

    async def get_active_for_bed(
        self, bed_id: uuid.UUID
    ) -> HoldRequest | None:
        """Return the single active (pending/approved) hold for a bed.

        The partial unique index ``idx_holds_active_bed`` guarantees at most
        one active hold per bed, so this returns at most one row.
        """
        stmt = (
            select(HoldRequest)
            .where(HoldRequest.bed_id == bed_id)
            .where(HoldRequest.status.in_(_ACTIVE_STATUSES))
            .where(HoldRequest.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def has_active_hold(
        self, bed_id: uuid.UUID, student_id: uuid.UUID
    ) -> bool:
        """Check if a student already has an active hold on a specific bed."""
        stmt = (
            select(func.count())
            .select_from(HoldRequest)
            .where(HoldRequest.bed_id == bed_id)
            .where(HoldRequest.student_id == student_id)
            .where(HoldRequest.status.in_(_ACTIVE_STATUSES))
            .where(HoldRequest.deleted_at.is_(None))
        )
        count = (await self._session.execute(stmt)).scalar() or 0
        return count > 0

    async def count_active_by_student(self, student_id: uuid.UUID) -> int:
        """Count all active holds across all beds for a student."""
        stmt = (
            select(func.count())
            .select_from(HoldRequest)
            .where(HoldRequest.student_id == student_id)
            .where(HoldRequest.status.in_(_ACTIVE_STATUSES))
            .where(HoldRequest.deleted_at.is_(None))
        )
        return (await self._session.execute(stmt)).scalar() or 0

    # ── List queries ─────────────────────────────────────────────────────────

    async def list_by_student(
        self,
        student_id: uuid.UUID,
        status: HoldStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[HoldRequest], int]:
        """Paginated hold requests for a student, optionally filtered by status.

        Returns:
            Tuple of (items, total_count).
        """
        base = (
            select(HoldRequest)
            .where(HoldRequest.student_id == student_id)
            .where(HoldRequest.deleted_at.is_(None))
        )
        if status is not None:
            base = base.where(HoldRequest.status == status.value)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            base.order_by(HoldRequest.requested_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def list_by_property(
        self,
        property_id: uuid.UUID,
        status: HoldStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[HoldRequest], int]:
        """Paginated hold requests for a property (owner view).

        Returns:
            Tuple of (items, total_count).
        """
        base = (
            select(HoldRequest)
            .where(HoldRequest.property_id == property_id)
            .where(HoldRequest.deleted_at.is_(None))
        )
        if status is not None:
            base = base.where(HoldRequest.status == status.value)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            base.order_by(HoldRequest.requested_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def list_by_bed(self, bed_id: uuid.UUID) -> list[HoldRequest]:
        """All non-deleted hold requests for a bed (any status), newest first."""
        stmt = (
            select(HoldRequest)
            .where(HoldRequest.bed_id == bed_id)
            .where(HoldRequest.deleted_at.is_(None))
            .order_by(HoldRequest.requested_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ── Expiry helpers ───────────────────────────────────────────────────────

    async def list_expired_approved(
        self, now: datetime | None = None
    ) -> list[HoldRequest]:
        """Fetch all approved holds whose ``expires_at`` is in the past.

        Used by the periodic expiry task to transition holds to EXPIRED.
        """
        if now is None:
            now = datetime.now(tz=timezone.utc)

        stmt = (
            select(HoldRequest)
            .where(HoldRequest.status == HoldStatus.APPROVED.value)
            .where(HoldRequest.expires_at <= now)
            .where(HoldRequest.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_expiring_soon(
        self, threshold: datetime
    ) -> list[HoldRequest]:
        """Fetch approved holds expiring before ``threshold`` but not yet expired.

        Used to send "hold expiring soon" notifications.
        """
        now = datetime.now(tz=timezone.utc)
        stmt = (
            select(HoldRequest)
            .where(HoldRequest.status == HoldStatus.APPROVED.value)
            .where(HoldRequest.expires_at > now)
            .where(HoldRequest.expires_at <= threshold)
            .where(HoldRequest.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ── Status transition ────────────────────────────────────────────────────

    async def update_status(
        self,
        hold_id: uuid.UUID,
        new_status: HoldStatus,
        *,
        resolved_by: uuid.UUID | None = None,
        resolution_note: str | None = None,
        approved_at: datetime | None = None,
        expires_at: datetime | None = None,
        resolved_at: datetime | None = None,
    ) -> HoldRequest | None:
        """Transition a hold request to a new status with optional metadata.

        Returns the updated record, or ``None`` if not found.
        """
        values: dict = {"status": new_status.value}
        if resolved_by is not None:
            values["resolved_by"] = resolved_by
        if resolution_note is not None:
            values["resolution_note"] = resolution_note
        if approved_at is not None:
            values["approved_at"] = approved_at
        if expires_at is not None:
            values["expires_at"] = expires_at
        if resolved_at is not None:
            values["resolved_at"] = resolved_at

        stmt = (
            update(HoldRequest)
            .where(HoldRequest.id == hold_id)
            .where(HoldRequest.deleted_at.is_(None))
            .values(**values)
            .returning(HoldRequest)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def bulk_expire(self, hold_ids: list[uuid.UUID]) -> int:
        """Batch-transition multiple holds to EXPIRED status.

        Returns the number of rows updated.
        """
        if not hold_ids:
            return 0

        now = datetime.now(tz=timezone.utc)
        stmt = (
            update(HoldRequest)
            .where(HoldRequest.id.in_(hold_ids))
            .where(HoldRequest.status == HoldStatus.APPROVED.value)
            .where(HoldRequest.deleted_at.is_(None))
            .values(
                status=HoldStatus.EXPIRED.value,
                resolved_at=now,
            )
        )
        result = await self._session.execute(stmt)
        return result.rowcount

    # ── Cooldown check ───────────────────────────────────────────────────────

    async def get_recent_resolved_for_bed(
        self,
        bed_id: uuid.UUID,
        student_id: uuid.UUID,
        since: datetime,
    ) -> HoldRequest | None:
        """Find a terminal-status hold on a specific bed by a specific student
        that was created after ``since``.

        Used for per-bed cooldown enforcement — prevents a student from
        re-requesting the same bed within a cooldown window.

        Args:
            bed_id:     The target bed.
            student_id: The requesting student.
            since:      Lower-bound timestamp (e.g., now - 30 minutes).

        Returns:
            The most recent matching hold, or ``None`` if no cooldown applies.
        """
        stmt = (
            select(HoldRequest)
            .where(HoldRequest.bed_id == bed_id)
            .where(HoldRequest.student_id == student_id)
            .where(HoldRequest.requested_at >= since)
            .where(HoldRequest.deleted_at.is_(None))
            .order_by(HoldRequest.requested_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
