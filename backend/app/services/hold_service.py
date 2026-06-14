"""Hold service — business logic for the hold request lifecycle.

Orchestrates hold creation, approval, rejection, cancellation, expiry,
and owner override.  Coordinates with WaitlistService, NotificationService,
and AuditService.

Phase 2 transaction convention: this service only ``flush()``es.
The calling router is responsible for ``commit()``.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError

from app.core.constants import (
    DEFAULT_HOLD_DURATION_HOURS,
    HOLD_COOLDOWN_MINUTES,
    MAX_ACTIVE_HOLDS_PER_STUDENT,
)
from app.core.enums import BedStatus, BookingStatus, HoldStatus
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.models.hold_request import HoldRequest
from app.repositories.bed_repository import BedRepository
from app.repositories.booking_repository import BookingRepository
from app.repositories.hold_request_repository import HoldRequestRepository
from app.repositories.property_repository import PropertyRepository
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.services.waitlist_service import WaitlistService

logger = logging.getLogger(__name__)


class HoldService:
    """Orchestrates the hold request lifecycle.

    Args:
        hold_repo:            Repository for hold_requests table.
        bed_repo:             Repository for beds table.
        booking_repo:         Repository for bookings table.
        property_repo:        Repository for properties table.
        waitlist_service:     Service for waitlist queue management.
        notification_service: Service for in-app notifications.
        audit_service:        Service for audit logging.
    """

    def __init__(
        self,
        hold_repo: HoldRequestRepository,
        bed_repo: BedRepository,
        booking_repo: BookingRepository,
        property_repo: PropertyRepository,
        waitlist_service: WaitlistService,
        notification_service: NotificationService,
        audit_service: AuditService,
    ) -> None:
        self._hold_repo = hold_repo
        self._bed_repo = bed_repo
        self._booking_repo = booking_repo
        self._property_repo = property_repo
        self._waitlist_service = waitlist_service
        self._notification_service = notification_service
        self._audit_service = audit_service

    # ── Request hold ─────────────────────────────────────────────────────────

    async def request_hold(
        self,
        *,
        bed_id: uuid.UUID,
        student_id: uuid.UUID,
        hold_duration_hours: int = DEFAULT_HOLD_DURATION_HOURS,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> HoldRequest | None:
        """Student requests a hold on a bed.

        Validates:
            1. Bed exists and is not soft-deleted.
            2. Per-bed 30-minute cooldown.
            3. Max 3 active holds per student.
            4. Student does not already have an active hold on this bed.
            5. If bed is VACANT → creates a PENDING hold.
            6. If bed is HELD/OCCUPIED → auto-adds to waitlist, returns ``None``.

        Args:
            bed_id:              Target bed UUID.
            student_id:          Requesting student UUID.
            hold_duration_hours: Requested hold duration (1-72h, default 24).
            ip_address:          Client IP for audit trail.
            user_agent:          Client user-agent for audit trail.

        Returns:
            The newly created HoldRequest if the bed was vacant, or ``None``
            if the student was added to the waitlist instead.

        Raises:
            NotFoundException:   Bed or property not found.
            BadRequestException: Cooldown active, hold limit reached, or duplicate hold.
            ConflictException:   Optimistic lock failure.
        """
        now = datetime.now(tz=timezone.utc)

        # 1. Acquire row-level lock on the bed
        bed = await self._bed_repo.get_for_update(bed_id)
        if bed is None:
            raise NotFoundException(
                message="Bed not found.",
                code="BED_NOT_FOUND",
            )

        # 2. Per-bed cooldown check
        cooldown_since = now - timedelta(minutes=HOLD_COOLDOWN_MINUTES)
        recent_hold = await self._hold_repo.get_recent_resolved_for_bed(
            bed_id=bed_id,
            student_id=student_id,
            since=cooldown_since,
        )
        if recent_hold is not None:
            raise BadRequestException(
                message="Please wait before requesting this bed again.",
                code="HOLD_COOLDOWN_ACTIVE",
            )

        # 3. Max active holds per student
        active_count = await self._hold_repo.count_active_by_student(student_id)
        if active_count >= MAX_ACTIVE_HOLDS_PER_STUDENT:
            raise BadRequestException(
                message=f"You can have at most {MAX_ACTIVE_HOLDS_PER_STUDENT} active holds.",
                code="MAX_HOLDS_REACHED",
            )

        # 4. Duplicate active hold check
        has_active = await self._hold_repo.has_active_hold(bed_id, student_id)
        if has_active:
            raise BadRequestException(
                message="You already have an active hold on this bed.",
                code="DUPLICATE_HOLD",
            )

        # 5. Fetch property for notifications
        prop = await self._property_repo.get(bed.property_id)
        if prop is None:
            raise NotFoundException(
                message="Property not found.",
                code="PROPERTY_NOT_FOUND",
            )

        bed_label = bed.label or bed.bed_number

        # 6. If bed is not VACANT → add to waitlist
        if bed.status != BedStatus.VACANT.value:
            await self._waitlist_service.add_to_waitlist(
                bed_id=bed_id,
                student_id=student_id,
                property_id=bed.property_id,
            )
            return None

        # 7. Bed is VACANT → create a PENDING hold
        try:
            hold = await self._hold_repo.create(
                bed_id=bed_id,
                student_id=student_id,
                property_id=bed.property_id,
                status=HoldStatus.PENDING.value,
                hold_duration_hours=hold_duration_hours,
            )
        except IntegrityError:
            # Partial unique index constraint — another hold was created concurrently
            raise ConflictException(
                message="This bed already has an active hold. Please retry.",
                code="HOLD_CONFLICT",
            )

        # 8. Update bed status → HELD (pending holds still reserve the bed visually)
        updated_bed = await self._bed_repo.update_status_optimistic(
            bed_id,
            bed.version,
            status=BedStatus.HELD.value,
            current_hold_id=hold.id,
        )
        if updated_bed is None:
            raise ConflictException(
                message="Bed status changed concurrently. Please retry.",
                code="OPTIMISTIC_LOCK_FAILURE",
            )

        # 9. Audit
        await self._audit_service.log_action(
            action="hold_requested",
            entity_type="hold_request",
            entity_id=hold.id,
            user_id=student_id,
            new_data={
                "bed_id": str(bed_id),
                "status": HoldStatus.PENDING.value,
                "hold_duration_hours": hold_duration_hours,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # 10. Notify owner
        await self._notification_service.notify_hold_requested(
            owner_id=prop.owner_id,
            student_id=student_id,
            bed_id=bed_id,
            property_name=prop.name,
            bed_label=bed_label,
        )

        return hold

    # ── Approve hold ─────────────────────────────────────────────────────────

    async def approve_hold(
        self,
        hold_id: uuid.UUID,
        owner_id: uuid.UUID,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> HoldRequest:
        """Owner approves a pending hold.

        Sets ``approved_at``, ``expires_at``, updates bed status → HELD.

        Args:
            hold_id:    The hold request to approve.
            owner_id:   The authenticated owner (for ownership validation).
            ip_address: Client IP for audit trail.
            user_agent: Client user-agent for audit trail.

        Returns:
            The updated HoldRequest.

        Raises:
            NotFoundException:   Hold or property not found.
            ForbiddenException:  Owner does not own the property.
            BadRequestException: Hold is not in PENDING status.
        """
        hold = await self._get_hold_or_raise(hold_id)
        await self._verify_property_ownership(hold.property_id, owner_id)

        if hold.status != HoldStatus.PENDING.value:
            raise BadRequestException(
                message="Only pending holds can be approved.",
                code="HOLD_NOT_PENDING",
            )

        now = datetime.now(tz=timezone.utc)
        expires_at = now + timedelta(hours=hold.hold_duration_hours)

        old_status = hold.status

        updated_hold = await self._hold_repo.update_status(
            hold_id,
            HoldStatus.APPROVED,
            resolved_by=owner_id,
            approved_at=now,
            expires_at=expires_at,
        )
        if updated_hold is None:
            raise NotFoundException(
                message="Hold request not found.",
                code="HOLD_NOT_FOUND",
            )

        # Bed should already be HELD from request_hold, but refresh the pointer
        bed = await self._bed_repo.get_for_update(hold.bed_id)
        if bed is not None:
            await self._bed_repo.update_status_optimistic(
                hold.bed_id,
                bed.version,
                status=BedStatus.HELD.value,
                current_hold_id=hold_id,
            )

        # Fetch property for notification
        prop = await self._property_repo.get(hold.property_id)
        bed_label = bed.label or bed.bed_number if bed else "Unknown"
        property_name = prop.name if prop else "Unknown"

        # Audit
        await self._audit_service.log_action(
            action="hold_approved",
            entity_type="hold_request",
            entity_id=hold_id,
            user_id=owner_id,
            old_data={"status": old_status},
            new_data={
                "status": HoldStatus.APPROVED.value,
                "approved_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Notify student
        await self._notification_service.notify_hold_approved(
            student_id=hold.student_id,
            bed_id=hold.bed_id,
            property_name=property_name,
            bed_label=bed_label,
            expires_at=expires_at.isoformat(),
        )

        return updated_hold

    # ── Reject hold ──────────────────────────────────────────────────────────

    async def reject_hold(
        self,
        hold_id: uuid.UUID,
        owner_id: uuid.UUID,
        *,
        resolution_note: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> HoldRequest:
        """Owner rejects a pending hold.

        Updates bed status → VACANT. **No waitlist promotion** (per decision #4).

        Args:
            hold_id:         The hold request to reject.
            owner_id:        The authenticated owner.
            resolution_note: Optional rejection reason.
            ip_address:      Client IP for audit trail.
            user_agent:      Client user-agent for audit trail.

        Returns:
            The updated HoldRequest.
        """
        hold = await self._get_hold_or_raise(hold_id)
        await self._verify_property_ownership(hold.property_id, owner_id)

        if hold.status != HoldStatus.PENDING.value:
            raise BadRequestException(
                message="Only pending holds can be rejected.",
                code="HOLD_NOT_PENDING",
            )

        now = datetime.now(tz=timezone.utc)
        old_status = hold.status

        updated_hold = await self._hold_repo.update_status(
            hold_id,
            HoldStatus.REJECTED,
            resolved_by=owner_id,
            resolution_note=resolution_note,
            resolved_at=now,
        )
        if updated_hold is None:
            raise NotFoundException(
                message="Hold request not found.",
                code="HOLD_NOT_FOUND",
            )

        # Release bed → VACANT (no waitlist promotion)
        bed = await self._bed_repo.get_for_update(hold.bed_id)
        if bed is not None and bed.current_hold_id == hold_id:
            await self._bed_repo.update_status_optimistic(
                hold.bed_id,
                bed.version,
                status=BedStatus.VACANT.value,
                current_hold_id=None,
            )

        # Fetch property for notification
        prop = await self._property_repo.get(hold.property_id)
        bed_obj = await self._bed_repo.get(hold.bed_id)
        bed_label = (bed_obj.label or bed_obj.bed_number) if bed_obj else "Unknown"
        property_name = prop.name if prop else "Unknown"

        # Audit
        await self._audit_service.log_action(
            action="hold_rejected",
            entity_type="hold_request",
            entity_id=hold_id,
            user_id=owner_id,
            old_data={"status": old_status},
            new_data={
                "status": HoldStatus.REJECTED.value,
                "resolution_note": resolution_note,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Notify student
        await self._notification_service.notify_hold_rejected(
            student_id=hold.student_id,
            bed_id=hold.bed_id,
            property_name=property_name,
            bed_label=bed_label,
            resolution_note=resolution_note,
        )

        return updated_hold

    # ── Cancel hold ──────────────────────────────────────────────────────────

    async def cancel_hold(
        self,
        hold_id: uuid.UUID,
        student_id: uuid.UUID,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> HoldRequest:
        """Student cancels their own hold. Triggers waitlist promotion.

        Args:
            hold_id:    The hold request to cancel.
            student_id: The authenticated student (ownership check).
            ip_address: Client IP for audit trail.
            user_agent: Client user-agent for audit trail.

        Returns:
            The updated HoldRequest.
        """
        hold = await self._get_hold_or_raise(hold_id)

        if hold.student_id != student_id:
            raise ForbiddenException(
                message="You can only cancel your own hold.",
                code="NOT_HOLD_OWNER",
            )

        if hold.status not in (HoldStatus.PENDING.value, HoldStatus.APPROVED.value):
            raise BadRequestException(
                message="Only active holds can be cancelled.",
                code="HOLD_NOT_ACTIVE",
            )

        now = datetime.now(tz=timezone.utc)
        old_status = hold.status

        updated_hold = await self._hold_repo.update_status(
            hold_id,
            HoldStatus.CANCELLED,
            resolved_by=student_id,
            resolved_at=now,
        )
        if updated_hold is None:
            raise NotFoundException(
                message="Hold request not found.",
                code="HOLD_NOT_FOUND",
            )

        # Release bed → VACANT
        bed = await self._bed_repo.get_for_update(hold.bed_id)
        if bed is not None and bed.current_hold_id == hold_id:
            await self._bed_repo.update_status_optimistic(
                hold.bed_id,
                bed.version,
                status=BedStatus.VACANT.value,
                current_hold_id=None,
            )

        # Audit
        await self._audit_service.log_action(
            action="hold_cancelled",
            entity_type="hold_request",
            entity_id=hold_id,
            user_id=student_id,
            old_data={"status": old_status},
            new_data={"status": HoldStatus.CANCELLED.value},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # ✅ Waitlist promotion (Decision #4: promote on cancellation)
        promoted_hold = await self._waitlist_service.promote_next(hold.bed_id)
        if promoted_hold is not None:
            prop = await self._property_repo.get(hold.property_id)
            bed_obj = await self._bed_repo.get(hold.bed_id)
            bed_label = (bed_obj.label or bed_obj.bed_number) if bed_obj else "Unknown"
            property_name = prop.name if prop else "Unknown"
            await self._notification_service.notify_waitlist_promoted(
                student_id=promoted_hold.student_id,
                bed_id=hold.bed_id,
                property_name=property_name,
                bed_label=bed_label,
                expires_at=promoted_hold.expires_at.isoformat() if promoted_hold.expires_at else "",
            )

        return updated_hold

    # ── Expire hold ──────────────────────────────────────────────────────────

    async def expire_hold(
        self,
        hold_id: uuid.UUID,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> HoldRequest:
        """System expires an approved hold past its TTL. Triggers waitlist promotion.

        Called by the future Celery periodic task.

        Args:
            hold_id:    The hold request to expire.
            ip_address: Client IP for audit trail.
            user_agent: Client user-agent for audit trail.

        Returns:
            The updated HoldRequest.
        """
        hold = await self._get_hold_or_raise(hold_id)

        if hold.status != HoldStatus.APPROVED.value:
            raise BadRequestException(
                message="Only approved holds can be expired.",
                code="HOLD_NOT_APPROVED",
            )

        now = datetime.now(tz=timezone.utc)
        old_status = hold.status

        updated_hold = await self._hold_repo.update_status(
            hold_id,
            HoldStatus.EXPIRED,
            resolved_at=now,
        )
        if updated_hold is None:
            raise NotFoundException(
                message="Hold request not found.",
                code="HOLD_NOT_FOUND",
            )

        # Release bed → VACANT
        bed = await self._bed_repo.get_for_update(hold.bed_id)
        if bed is not None and bed.current_hold_id == hold_id:
            await self._bed_repo.update_status_optimistic(
                hold.bed_id,
                bed.version,
                status=BedStatus.VACANT.value,
                current_hold_id=None,
            )

        # Fetch property for notification
        prop = await self._property_repo.get(hold.property_id)
        bed_obj = await self._bed_repo.get(hold.bed_id)
        bed_label = (bed_obj.label or bed_obj.bed_number) if bed_obj else "Unknown"
        property_name = prop.name if prop else "Unknown"

        # Audit
        await self._audit_service.log_action(
            action="hold_expired",
            entity_type="hold_request",
            entity_id=hold_id,
            old_data={"status": old_status},
            new_data={"status": HoldStatus.EXPIRED.value},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Notify student
        await self._notification_service.notify_hold_expired(
            student_id=hold.student_id,
            bed_id=hold.bed_id,
            property_name=property_name,
            bed_label=bed_label,
        )

        # ✅ Waitlist promotion (Decision #4: promote on expiry)
        promoted_hold = await self._waitlist_service.promote_next(hold.bed_id)
        if promoted_hold is not None:
            await self._notification_service.notify_waitlist_promoted(
                student_id=promoted_hold.student_id,
                bed_id=hold.bed_id,
                property_name=property_name,
                bed_label=bed_label,
                expires_at=promoted_hold.expires_at.isoformat() if promoted_hold.expires_at else "",
            )

        return updated_hold

    # ── Override hold ────────────────────────────────────────────────────────

    async def override_hold(
        self,
        hold_id: uuid.UUID,
        owner_id: uuid.UUID,
        target_student_id: uuid.UUID,
        *,
        check_in_date=None,
        check_out_date=None,
        notes: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ):
        """Owner overrides an existing hold for a different student's booking.

        Sequence:
            1. Validate hold is active (pending/approved).
            2. Lock the bed row.
            3. Transition hold → OVERRIDDEN.
            4. Create a new Booking for ``target_student_id``.
            5. Update bed → OCCUPIED with new booking pointer.
            6. Cancel all waitlist entries for this bed.
            7. Audit both the override and the new booking.
            8. Notify original student (overridden) and target student (booking confirmed).

        Args:
            hold_id:            The hold to override.
            owner_id:           The authenticated owner.
            target_student_id:  The student to book for.
            check_in_date:      Optional check-in date for the booking.
            check_out_date:     Optional check-out date for the booking.
            notes:              Optional notes for the booking.
            ip_address:         Client IP for audit trail.
            user_agent:         Client user-agent for audit trail.

        Returns:
            A tuple of (overridden HoldRequest, new Booking).
        """
        hold = await self._get_hold_or_raise(hold_id)
        await self._verify_property_ownership(hold.property_id, owner_id)

        if hold.status not in (HoldStatus.PENDING.value, HoldStatus.APPROVED.value):
            raise BadRequestException(
                message="Only active holds can be overridden.",
                code="HOLD_NOT_ACTIVE",
            )

        now = datetime.now(tz=timezone.utc)
        old_status = hold.status

        # 1. Lock bed
        bed = await self._bed_repo.get_for_update(hold.bed_id)
        if bed is None:
            raise NotFoundException(
                message="Bed not found.",
                code="BED_NOT_FOUND",
            )

        # 2. Transition hold → OVERRIDDEN
        updated_hold = await self._hold_repo.update_status(
            hold_id,
            HoldStatus.OVERRIDDEN,
            resolved_by=owner_id,
            resolved_at=now,
            resolution_note=f"Overridden: bed assigned to another student.",
        )
        if updated_hold is None:
            raise NotFoundException(
                message="Hold request not found.",
                code="HOLD_NOT_FOUND",
            )

        # 3. Create booking for target student
        booking = await self._booking_repo.create(
            bed_id=hold.bed_id,
            student_id=target_student_id,
            property_id=hold.property_id,
            hold_request_id=None,  # Direct booking — not from this hold
            status=BookingStatus.CONFIRMED.value,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            notes=notes,
        )

        # 4. Update bed → OCCUPIED
        updated_bed = await self._bed_repo.update_status_optimistic(
            hold.bed_id,
            bed.version,
            status=BedStatus.OCCUPIED.value,
            current_hold_id=None,
            current_booking_id=booking.id,
        )
        if updated_bed is None:
            raise ConflictException(
                message="Bed status changed concurrently. Please retry.",
                code="OPTIMISTIC_LOCK_FAILURE",
            )

        # 5. Cancel all waitlist entries
        await self._waitlist_service.cancel_all_for_bed(hold.bed_id)

        # Fetch property for notifications
        prop = await self._property_repo.get(hold.property_id)
        bed_label = bed.label or bed.bed_number
        property_name = prop.name if prop else "Unknown"

        # 6. Audit — hold overridden
        await self._audit_service.log_action(
            action="hold_overridden",
            entity_type="hold_request",
            entity_id=hold_id,
            user_id=owner_id,
            old_data={"status": old_status},
            new_data={
                "status": HoldStatus.OVERRIDDEN.value,
                "target_student_id": str(target_student_id),
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # 7. Audit — booking confirmed
        await self._audit_service.log_action(
            action="booking_confirmed",
            entity_type="booking",
            entity_id=booking.id,
            user_id=owner_id,
            new_data={
                "bed_id": str(hold.bed_id),
                "student_id": str(target_student_id),
                "source": "override",
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # 8. Notify original student (hold overridden)
        await self._notification_service.notify_hold_overridden(
            student_id=hold.student_id,
            bed_id=hold.bed_id,
            property_name=property_name,
            bed_label=bed_label,
        )

        # 9. Notify target student (booking confirmed)
        await self._notification_service.notify_booking_confirmed(
            student_id=target_student_id,
            bed_id=hold.bed_id,
            property_name=property_name,
            bed_label=bed_label,
        )

        return updated_hold, booking

    # ── Read helpers ─────────────────────────────────────────────────────────

    async def get_hold(self, hold_id: uuid.UUID) -> HoldRequest:
        """Fetch a single hold with eager-loaded relations."""
        hold = await self._hold_repo.get_with_relations(hold_id)
        if hold is None:
            raise NotFoundException(
                message="Hold request not found.",
                code="HOLD_NOT_FOUND",
            )
        return hold

    async def list_student_holds(
        self,
        student_id: uuid.UUID,
        *,
        status: HoldStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[HoldRequest], int]:
        """Paginated holds for the authenticated student."""
        return await self._hold_repo.list_by_student(
            student_id, status=status, page=page, page_size=page_size
        )

    async def list_property_holds(
        self,
        property_id: uuid.UUID,
        owner_id: uuid.UUID,
        *,
        status: HoldStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[HoldRequest], int]:
        """Paginated holds for a property (owner view)."""
        await self._verify_property_ownership(property_id, owner_id)
        return await self._hold_repo.list_by_property(
            property_id, status=status, page=page, page_size=page_size
        )

    # ── Internal helpers ─────────────────────────────────────────────────────

    async def _get_hold_or_raise(self, hold_id: uuid.UUID) -> HoldRequest:
        """Fetch a hold, raising NotFoundException if missing."""
        hold = await self._hold_repo.get(hold_id)
        if hold is None:
            raise NotFoundException(
                message="Hold request not found.",
                code="HOLD_NOT_FOUND",
            )
        return hold

    async def _verify_property_ownership(
        self, property_id: uuid.UUID, owner_id: uuid.UUID
    ) -> None:
        """Verify that the user owns the parent property."""
        prop = await self._property_repo.get(property_id)
        if prop is None or prop.is_deleted:
            raise NotFoundException(
                message="Property not found.",
                code="PROPERTY_NOT_FOUND",
            )
        if prop.owner_id != owner_id:
            raise ForbiddenException(
                message="You do not own this property.",
                code="NOT_PROPERTY_OWNER",
            )
