"""Waitlist service — business logic for FIFO bed waitlist management.

Manages queue state: add, promote, cancel, reposition.
Does NOT directly call NotificationService — notification orchestration
is the responsibility of HoldService and BookingService which invoke
WaitlistService methods.

Phase 2 transaction convention: this service only ``flush()``es.
The calling router is responsible for ``commit()``.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from app.core.constants import DEFAULT_HOLD_DURATION_HOURS
from app.core.enums import BedStatus, HoldStatus, WaitlistStatus
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.models.hold_request import HoldRequest
from app.models.waitlist_entry import WaitlistEntry
from app.repositories.bed_repository import BedRepository
from app.repositories.hold_request_repository import HoldRequestRepository
from app.repositories.waitlist_entry_repository import WaitlistEntryRepository
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class WaitlistService:
    """Orchestrates bed waitlist queue management.

    Args:
        waitlist_repo: Repository for waitlist_entries table.
        hold_repo:     Repository for hold_requests table.
        bed_repo:      Repository for beds table.
        audit_service: Service for audit logging.
    """

    def __init__(
        self,
        waitlist_repo: WaitlistEntryRepository,
        hold_repo: HoldRequestRepository,
        bed_repo: BedRepository,
        audit_service: AuditService,
    ) -> None:
        self._waitlist_repo = waitlist_repo
        self._hold_repo = hold_repo
        self._bed_repo = bed_repo
        self._audit_service = audit_service

    # ── Add to waitlist ──────────────────────────────────────────────────────

    async def add_to_waitlist(
        self,
        *,
        bed_id: uuid.UUID,
        student_id: uuid.UUID,
        property_id: uuid.UUID,
    ) -> WaitlistEntry:
        """Add a student to a bed's waitlist queue.

        Validates that the student is not already in the queue.
        Auto-assigns the next FIFO position.

        Args:
            bed_id:      The target bed.
            student_id:  The requesting student.
            property_id: The parent property (denormalized).

        Returns:
            The newly created WaitlistEntry.

        Raises:
            BadRequestException: If the student is already in the queue.
        """
        # Duplicate guard
        already_queued = await self._waitlist_repo.is_student_in_queue(
            bed_id, student_id
        )
        if already_queued:
            raise BadRequestException(
                message="You are already on the waitlist for this bed.",
                code="ALREADY_IN_WAITLIST",
            )

        position = await self._waitlist_repo.next_position(bed_id)

        entry = await self._waitlist_repo.create(
            bed_id=bed_id,
            student_id=student_id,
            property_id=property_id,
            position=position,
            status=WaitlistStatus.ACTIVE.value,
        )

        await self._audit_service.log_action(
            action="waitlist_joined",
            entity_type="waitlist_entry",
            entity_id=entry.id,
            user_id=student_id,
            new_data={"bed_id": str(bed_id), "position": position},
        )

        return entry

    # ── Promote next in queue ────────────────────────────────────────────────

    async def promote_next(
        self,
        bed_id: uuid.UUID,
    ) -> HoldRequest | None:
        """Promote the front-of-queue student to a new auto-approved hold.

        Creates a new HoldRequest with status APPROVED, 24h expiry,
        updates the bed status to HELD, and repositions the remaining queue.

        Called by HoldService on hold expiry/cancellation and
        BookingService on booking vacancy/cancellation.

        Args:
            bed_id: The bed whose waitlist to promote from.

        Returns:
            The newly created auto-approved HoldRequest, or ``None``
            if the waitlist is empty.
        """
        next_entry = await self._waitlist_repo.get_next_in_queue(bed_id)
        if next_entry is None:
            return None

        # Promote the waitlist entry
        promoted = await self._waitlist_repo.promote(next_entry.id)
        if promoted is None:
            # Concurrent modification — entry was already promoted/cancelled
            logger.warning("Waitlist entry %s already consumed", next_entry.id)
            return None

        # Reposition remaining queue entries
        await self._waitlist_repo.reposition_after_removal(
            bed_id, promoted.position
        )

        # Create an auto-approved hold for the promoted student
        now = datetime.now(tz=timezone.utc)
        expires_at = now + timedelta(hours=DEFAULT_HOLD_DURATION_HOURS)

        hold = await self._hold_repo.create(
            bed_id=bed_id,
            student_id=promoted.student_id,
            property_id=promoted.property_id,
            status=HoldStatus.APPROVED.value,
            hold_duration_hours=DEFAULT_HOLD_DURATION_HOURS,
            approved_at=now,
            expires_at=expires_at,
        )

        # Update bed status → HELD with the new hold
        bed = await self._bed_repo.get_for_update(bed_id)
        if bed is None:
            raise NotFoundException(
                message="Bed not found.",
                code="BED_NOT_FOUND",
            )

        updated_bed = await self._bed_repo.update_status_optimistic(
            bed_id,
            bed.version,
            status=BedStatus.HELD.value,
            current_hold_id=hold.id,
            current_booking_id=None,
        )
        if updated_bed is None:
            raise ConflictException(
                message="Bed status changed concurrently. Please retry.",
                code="OPTIMISTIC_LOCK_FAILURE",
            )

        # Audit
        await self._audit_service.log_action(
            action="waitlist_promoted",
            entity_type="waitlist_entry",
            entity_id=promoted.id,
            user_id=promoted.student_id,
            old_data={"status": WaitlistStatus.ACTIVE.value},
            new_data={"status": WaitlistStatus.PROMOTED.value},
        )

        return hold

    # ── Cancel entry ─────────────────────────────────────────────────────────

    async def cancel_entry(
        self,
        entry_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> WaitlistEntry:
        """Student cancels their own waitlist entry. Repositions remaining queue.

        Args:
            entry_id:   The waitlist entry to cancel.
            student_id: The authenticated student (for ownership check).

        Returns:
            The cancelled WaitlistEntry.

        Raises:
            NotFoundException: If the entry does not exist.
            ForbiddenException: If the student does not own the entry.
        """
        entry = await self._waitlist_repo.get(entry_id)
        if entry is None:
            raise NotFoundException(
                message="Waitlist entry not found.",
                code="WAITLIST_ENTRY_NOT_FOUND",
            )
        if entry.student_id != student_id:
            from app.core.exceptions import ForbiddenException
            raise ForbiddenException(
                message="You can only cancel your own waitlist entry.",
                code="NOT_WAITLIST_OWNER",
            )
        if entry.status != WaitlistStatus.ACTIVE.value:
            raise BadRequestException(
                message="Only active waitlist entries can be cancelled.",
                code="WAITLIST_NOT_ACTIVE",
            )

        cancelled = await self._waitlist_repo.cancel(entry_id)
        if cancelled is None:
            raise BadRequestException(
                message="Waitlist entry could not be cancelled.",
                code="WAITLIST_CANCEL_FAILED",
            )

        # Close position gap
        await self._waitlist_repo.reposition_after_removal(
            entry.bed_id, entry.position
        )

        await self._audit_service.log_action(
            action="waitlist_cancelled",
            entity_type="waitlist_entry",
            entity_id=entry_id,
            user_id=student_id,
            old_data={"status": WaitlistStatus.ACTIVE.value, "position": entry.position},
            new_data={"status": WaitlistStatus.CANCELLED.value},
        )

        return cancelled

    # ── Bulk cancel ──────────────────────────────────────────────────────────

    async def cancel_all_for_bed(self, bed_id: uuid.UUID) -> int:
        """Bulk-cancel all active waitlist entries for a bed.

        Used when a bed is directly booked or an override occurs.

        Returns:
            The number of entries cancelled.
        """
        return await self._waitlist_repo.cancel_all_for_bed(bed_id)

    # ── Read helpers ─────────────────────────────────────────────────────────

    async def get_queue_position(
        self, bed_id: uuid.UUID, student_id: uuid.UUID
    ) -> int | None:
        """Get a student's current position in a bed's waitlist.

        Returns:
            The position (1-indexed), or ``None`` if the student is not in the queue.
        """
        entries = await self._waitlist_repo.list_active_for_bed(bed_id)
        for entry in entries:
            if entry.student_id == student_id:
                return entry.position
        return None

    async def list_student_entries(
        self,
        student_id: uuid.UUID,
        *,
        status: WaitlistStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[WaitlistEntry], int]:
        """Paginated waitlist entries for the authenticated student."""
        return await self._waitlist_repo.list_by_student(
            student_id, status=status, page=page, page_size=page_size
        )

    async def list_bed_queue(self, bed_id: uuid.UUID) -> list[WaitlistEntry]:
        """Ordered active queue for a bed."""
        return await self._waitlist_repo.list_active_for_bed(bed_id)
