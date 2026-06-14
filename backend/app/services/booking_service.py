"""Booking service — business logic for the booking lifecycle.

Orchestrates hold-to-booking conversion, direct bookings, vacate,
and cancel operations.  Coordinates with WaitlistService,
NotificationService, and AuditService.

Phase 2 transaction convention: this service only ``flush()``es.
The calling router is responsible for ``commit()``.
"""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timezone

from app.core.enums import BedStatus, BookingStatus, HoldStatus
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.models.booking import Booking
from app.repositories.bed_repository import BedRepository
from app.repositories.booking_repository import BookingRepository
from app.repositories.hold_request_repository import HoldRequestRepository
from app.repositories.property_repository import PropertyRepository
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.services.waitlist_service import WaitlistService

logger = logging.getLogger(__name__)


class BookingService:
    """Orchestrates the booking lifecycle.

    Args:
        booking_repo:         Repository for bookings table.
        hold_repo:            Repository for hold_requests table.
        bed_repo:             Repository for beds table.
        property_repo:        Repository for properties table.
        waitlist_service:     Service for waitlist queue management.
        notification_service: Service for in-app notifications.
        audit_service:        Service for audit logging.
    """

    def __init__(
        self,
        booking_repo: BookingRepository,
        hold_repo: HoldRequestRepository,
        bed_repo: BedRepository,
        property_repo: PropertyRepository,
        waitlist_service: WaitlistService,
        notification_service: NotificationService,
        audit_service: AuditService,
    ) -> None:
        self._booking_repo = booking_repo
        self._hold_repo = hold_repo
        self._bed_repo = bed_repo
        self._property_repo = property_repo
        self._waitlist_service = waitlist_service
        self._notification_service = notification_service
        self._audit_service = audit_service

    # ── Create from hold ─────────────────────────────────────────────────────

    async def create_from_hold(
        self,
        hold_id: uuid.UUID,
        owner_id: uuid.UUID,
        *,
        check_in_date: date | None = None,
        check_out_date: date | None = None,
        notes: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Booking:
        """Convert an approved hold into a confirmed booking.

        Updates bed status → OCCUPIED, sets ``current_booking_id``,
        and cancels all remaining waitlist entries for the bed.

        Args:
            hold_id:        The approved hold to convert.
            owner_id:       The authenticated owner (for ownership validation).
            check_in_date:  Optional check-in date.
            check_out_date: Optional check-out date.
            notes:          Optional booking notes.
            ip_address:     Client IP for audit trail.
            user_agent:     Client user-agent for audit trail.

        Returns:
            The newly created Booking.

        Raises:
            NotFoundException:   Hold, bed, or property not found.
            ForbiddenException:  Owner does not own the property.
            BadRequestException: Hold is not APPROVED.
            ConflictException:   Optimistic lock failure.
        """
        # Validate hold
        hold = await self._hold_repo.get(hold_id)
        if hold is None:
            raise NotFoundException(
                message="Hold request not found.",
                code="HOLD_NOT_FOUND",
            )

        await self._verify_property_ownership(hold.property_id, owner_id)

        if hold.status != HoldStatus.APPROVED.value:
            raise BadRequestException(
                message="Only approved holds can be converted to bookings.",
                code="HOLD_NOT_APPROVED",
            )

        # Check no existing booking from this hold
        existing = await self._booking_repo.get_by_hold_request(hold_id)
        if existing is not None:
            raise BadRequestException(
                message="A booking already exists for this hold request.",
                code="BOOKING_ALREADY_EXISTS",
            )

        # Lock bed
        bed = await self._bed_repo.get_for_update(hold.bed_id)
        if bed is None:
            raise NotFoundException(
                message="Bed not found.",
                code="BED_NOT_FOUND",
            )

        # Create booking
        booking = await self._booking_repo.create(
            bed_id=hold.bed_id,
            student_id=hold.student_id,
            property_id=hold.property_id,
            hold_request_id=hold_id,
            status=BookingStatus.CONFIRMED.value,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            notes=notes,
        )

        # Transition hold to a terminal state (it's been consumed)
        now = datetime.now(tz=timezone.utc)
        await self._hold_repo.update_status(
            hold_id,
            HoldStatus.EXPIRED,  # Consumed — functionally complete
            resolved_by=owner_id,
            resolved_at=now,
            resolution_note="Converted to booking.",
        )

        # Update bed → OCCUPIED
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

        # Cancel all waitlist entries for this bed
        await self._waitlist_service.cancel_all_for_bed(hold.bed_id)

        # Fetch property for notification
        prop = await self._property_repo.get(hold.property_id)
        bed_label = bed.label or bed.bed_number
        property_name = prop.name if prop else "Unknown"

        # Audit
        await self._audit_service.log_action(
            action="booking_confirmed",
            entity_type="booking",
            entity_id=booking.id,
            user_id=owner_id,
            new_data={
                "bed_id": str(hold.bed_id),
                "student_id": str(hold.student_id),
                "hold_request_id": str(hold_id),
                "source": "hold_conversion",
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Notify student
        await self._notification_service.notify_booking_confirmed(
            student_id=hold.student_id,
            bed_id=hold.bed_id,
            property_name=property_name,
            bed_label=bed_label,
        )

        return booking

    # ── Create direct ────────────────────────────────────────────────────────

    async def create_direct(
        self,
        *,
        bed_id: uuid.UUID,
        student_id: uuid.UUID,
        owner_id: uuid.UUID,
        check_in_date: date | None = None,
        check_out_date: date | None = None,
        notes: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Booking:
        """Owner creates a booking directly (no hold).

        Updates bed status → OCCUPIED, cancels all waitlist entries.

        Args:
            bed_id:         Target bed UUID.
            student_id:     The student being booked for.
            owner_id:       The authenticated owner.
            check_in_date:  Optional check-in date.
            check_out_date: Optional check-out date.
            notes:          Optional booking notes.
            ip_address:     Client IP for audit trail.
            user_agent:     Client user-agent for audit trail.

        Returns:
            The newly created Booking.
        """
        # Lock bed
        bed = await self._bed_repo.get_for_update(bed_id)
        if bed is None:
            raise NotFoundException(
                message="Bed not found.",
                code="BED_NOT_FOUND",
            )

        await self._verify_property_ownership(bed.property_id, owner_id)

        # Check bed is not already occupied
        active_booking = await self._booking_repo.get_active_for_bed(bed_id)
        if active_booking is not None:
            raise BadRequestException(
                message="This bed already has an active booking.",
                code="BED_ALREADY_BOOKED",
            )

        # Create booking
        booking = await self._booking_repo.create(
            bed_id=bed_id,
            student_id=student_id,
            property_id=bed.property_id,
            hold_request_id=None,
            status=BookingStatus.CONFIRMED.value,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            notes=notes,
        )

        # Update bed → OCCUPIED
        updated_bed = await self._bed_repo.update_status_optimistic(
            bed_id,
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

        # Cancel all waitlist entries for this bed
        await self._waitlist_service.cancel_all_for_bed(bed_id)

        # Fetch property for notification
        prop = await self._property_repo.get(bed.property_id)
        bed_label = bed.label or bed.bed_number
        property_name = prop.name if prop else "Unknown"

        # Audit
        await self._audit_service.log_action(
            action="booking_confirmed",
            entity_type="booking",
            entity_id=booking.id,
            user_id=owner_id,
            new_data={
                "bed_id": str(bed_id),
                "student_id": str(student_id),
                "source": "direct",
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Notify student
        await self._notification_service.notify_booking_confirmed(
            student_id=student_id,
            bed_id=bed_id,
            property_name=property_name,
            bed_label=bed_label,
        )

        return booking

    # ── Vacate ───────────────────────────────────────────────────────────────

    async def vacate(
        self,
        booking_id: uuid.UUID,
        owner_id: uuid.UUID,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Booking:
        """Owner marks a booking as vacated. Triggers waitlist promotion.

        Args:
            booking_id: The booking to vacate.
            owner_id:   The authenticated owner.
            ip_address: Client IP for audit trail.
            user_agent: Client user-agent for audit trail.

        Returns:
            The updated Booking.
        """
        booking = await self._get_booking_or_raise(booking_id)
        await self._verify_property_ownership(booking.property_id, owner_id)

        if booking.status != BookingStatus.CONFIRMED.value:
            raise BadRequestException(
                message="Only confirmed bookings can be vacated.",
                code="BOOKING_NOT_CONFIRMED",
            )

        old_status = booking.status

        vacated = await self._booking_repo.vacate(booking_id)
        if vacated is None:
            raise NotFoundException(
                message="Booking not found.",
                code="BOOKING_NOT_FOUND",
            )

        # Release bed → VACANT
        bed = await self._bed_repo.get_for_update(booking.bed_id)
        if bed is not None and bed.current_booking_id == booking_id:
            await self._bed_repo.update_status_optimistic(
                booking.bed_id,
                bed.version,
                status=BedStatus.VACANT.value,
                current_booking_id=None,
                current_hold_id=None,
            )

        # Audit
        await self._audit_service.log_action(
            action="booking_vacated",
            entity_type="booking",
            entity_id=booking_id,
            user_id=owner_id,
            old_data={"status": old_status},
            new_data={"status": BookingStatus.VACATED.value},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # ✅ Waitlist promotion (Decision #4: promote on vacancy)
        promoted_hold = await self._waitlist_service.promote_next(booking.bed_id)
        if promoted_hold is not None:
            prop = await self._property_repo.get(booking.property_id)
            bed_obj = await self._bed_repo.get(booking.bed_id)
            bed_label = (bed_obj.label or bed_obj.bed_number) if bed_obj else "Unknown"
            property_name = prop.name if prop else "Unknown"
            await self._notification_service.notify_waitlist_promoted(
                student_id=promoted_hold.student_id,
                bed_id=booking.bed_id,
                property_name=property_name,
                bed_label=bed_label,
                expires_at=promoted_hold.expires_at.isoformat() if promoted_hold.expires_at else "",
            )

        return vacated

    # ── Cancel ───────────────────────────────────────────────────────────────

    async def cancel(
        self,
        booking_id: uuid.UUID,
        owner_id: uuid.UUID,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Booking:
        """Cancel a confirmed booking. Triggers waitlist promotion.

        Args:
            booking_id: The booking to cancel.
            owner_id:   The authenticated owner.
            ip_address: Client IP for audit trail.
            user_agent: Client user-agent for audit trail.

        Returns:
            The updated Booking.
        """
        booking = await self._get_booking_or_raise(booking_id)
        await self._verify_property_ownership(booking.property_id, owner_id)

        if booking.status != BookingStatus.CONFIRMED.value:
            raise BadRequestException(
                message="Only confirmed bookings can be cancelled.",
                code="BOOKING_NOT_CONFIRMED",
            )

        old_status = booking.status

        cancelled = await self._booking_repo.cancel(booking_id)
        if cancelled is None:
            raise NotFoundException(
                message="Booking not found.",
                code="BOOKING_NOT_FOUND",
            )

        # Release bed → VACANT
        bed = await self._bed_repo.get_for_update(booking.bed_id)
        if bed is not None and bed.current_booking_id == booking_id:
            await self._bed_repo.update_status_optimistic(
                booking.bed_id,
                bed.version,
                status=BedStatus.VACANT.value,
                current_booking_id=None,
                current_hold_id=None,
            )

        # Audit
        await self._audit_service.log_action(
            action="booking_cancelled",
            entity_type="booking",
            entity_id=booking_id,
            user_id=owner_id,
            old_data={"status": old_status},
            new_data={"status": BookingStatus.CANCELLED.value},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # ✅ Waitlist promotion (Decision #4: promote on booking cancellation)
        promoted_hold = await self._waitlist_service.promote_next(booking.bed_id)
        if promoted_hold is not None:
            prop = await self._property_repo.get(booking.property_id)
            bed_obj = await self._bed_repo.get(booking.bed_id)
            bed_label = (bed_obj.label or bed_obj.bed_number) if bed_obj else "Unknown"
            property_name = prop.name if prop else "Unknown"
            await self._notification_service.notify_waitlist_promoted(
                student_id=promoted_hold.student_id,
                bed_id=booking.bed_id,
                property_name=property_name,
                bed_label=bed_label,
                expires_at=promoted_hold.expires_at.isoformat() if promoted_hold.expires_at else "",
            )

        return cancelled

    # ── Read helpers ─────────────────────────────────────────────────────────

    async def get_booking(self, booking_id: uuid.UUID) -> Booking:
        """Fetch a single booking with eager-loaded relations."""
        booking = await self._booking_repo.get_with_relations(booking_id)
        if booking is None:
            raise NotFoundException(
                message="Booking not found.",
                code="BOOKING_NOT_FOUND",
            )
        return booking

    async def list_student_bookings(
        self,
        student_id: uuid.UUID,
        *,
        status: BookingStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Booking], int]:
        """Paginated bookings for the authenticated student."""
        return await self._booking_repo.list_by_student(
            student_id, status=status, page=page, page_size=page_size
        )

    async def list_property_bookings(
        self,
        property_id: uuid.UUID,
        owner_id: uuid.UUID,
        *,
        status: BookingStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Booking], int]:
        """Paginated bookings for a property (owner view)."""
        await self._verify_property_ownership(property_id, owner_id)
        return await self._booking_repo.list_by_property(
            property_id, status=status, page=page, page_size=page_size
        )

    # ── Internal helpers ─────────────────────────────────────────────────────

    async def _get_booking_or_raise(self, booking_id: uuid.UUID) -> Booking:
        """Fetch a booking, raising NotFoundException if missing."""
        booking = await self._booking_repo.get(booking_id)
        if booking is None:
            raise NotFoundException(
                message="Booking not found.",
                code="BOOKING_NOT_FOUND",
            )
        return booking

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
