"""Tests for database-level audit log creation on holds/bookings state updates.

Validates that HoldService and BookingService trigger AuditService.log_action
calls for all lifecycle milestones.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.enums import BedStatus, BookingStatus, HoldStatus
from app.services.booking_service import BookingService
from app.services.hold_service import HoldService


@pytest.mark.asyncio
async def test_hold_service_approve_writes_audit_log() -> None:
    """Verify HoldService.approve_hold triggers an audit log entry."""
    # Setup mocks
    mock_hold_repo = AsyncMock()
    mock_bed_repo = AsyncMock()
    mock_booking_repo = AsyncMock()
    mock_property_repo = AsyncMock()
    mock_waitlist_service = AsyncMock()
    mock_notification_service = AsyncMock()
    mock_audit_service = AsyncMock()

    # Stub hold request retrieval
    hold_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    student_id = uuid.uuid4()
    bed_id = uuid.uuid4()
    prop_id = uuid.uuid4()

    mock_hold = MagicMock()
    mock_hold.id = hold_id
    mock_hold.student_id = student_id
    mock_hold.bed_id = bed_id
    mock_hold.property_id = prop_id
    mock_hold.status = HoldStatus.PENDING.value
    mock_hold.hold_duration_hours = 24
    mock_hold_repo.get.return_value = mock_hold
    mock_hold_repo.update.return_value = mock_hold

    # Stub bed retrieval and property ownership
    mock_bed = MagicMock()
    mock_bed.id = bed_id
    mock_bed.status = BedStatus.VACANT.value
    mock_bed.label = "Bed A"
    mock_bed.is_deleted = False
    mock_bed_repo.get.return_value = mock_bed

    mock_property = MagicMock()
    mock_property.id = prop_id
    mock_property.owner_id = owner_id
    mock_property.name = "Cozy PG"
    mock_property.is_deleted = False
    mock_property_repo.get.return_value = mock_property

    # Instantiate HoldService
    service = HoldService(
        hold_repo=mock_hold_repo,
        bed_repo=mock_bed_repo,
        booking_repo=mock_booking_repo,
        property_repo=mock_property_repo,
        waitlist_service=mock_waitlist_service,
        notification_service=mock_notification_service,
        audit_service=mock_audit_service,
    )

    # Call method
    await service.approve_hold(
        hold_id=hold_id,
        owner_id=owner_id,
        ip_address="127.0.0.1",
        user_agent="TestAgent",
    )

    # Assert audit service was invoked with correct attributes
    mock_audit_service.log_action.assert_called_once()
    call_kwargs = mock_audit_service.log_action.call_args.kwargs
    assert call_kwargs["action"] == "hold_approved"
    assert call_kwargs["entity_type"] == "hold_request"
    assert call_kwargs["entity_id"] == hold_id
    assert call_kwargs["user_id"] == owner_id
    assert call_kwargs["old_data"] == {"status": "pending"}
    assert call_kwargs["new_data"]["status"] == "approved"
    assert "approved_at" in call_kwargs["new_data"]
    assert "expires_at" in call_kwargs["new_data"]
    assert call_kwargs["ip_address"] == "127.0.0.1"
    assert call_kwargs["user_agent"] == "TestAgent"


@pytest.mark.asyncio
async def test_booking_service_confirm_writes_audit_log() -> None:
    """Verify BookingService.create_from_hold triggers an audit log entry."""
    # Setup mocks
    mock_booking_repo = AsyncMock()
    mock_hold_repo = MagicMock()  # Hold repo uses regular mocks or AsyncMocks as needed
    mock_hold_repo_async = AsyncMock()
    mock_bed_repo = AsyncMock()
    mock_property_repo = AsyncMock()
    mock_waitlist_service = AsyncMock()
    mock_notification_service = AsyncMock()
    mock_audit_service = AsyncMock()
    mock_user_repo = AsyncMock()

    # Stub values
    hold_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    student_id = uuid.uuid4()
    bed_id = uuid.uuid4()
    prop_id = uuid.uuid4()
    booking_id = uuid.uuid4()

    mock_hold = MagicMock()
    mock_hold.id = hold_id
    mock_hold.student_id = student_id
    mock_hold.bed_id = bed_id
    mock_hold.property_id = prop_id
    mock_hold.status = HoldStatus.APPROVED.value
    mock_hold.is_deleted = False
    mock_hold_repo_async.get.return_value = mock_hold

    mock_bed = MagicMock()
    mock_bed.id = bed_id
    mock_bed.status = BedStatus.HELD.value
    mock_bed.label = "Bed 101"
    mock_bed.is_deleted = False
    mock_bed_repo.get.return_value = mock_bed

    mock_property = MagicMock()
    mock_property.id = prop_id
    mock_property.owner_id = owner_id
    mock_property.name = "Luxury PG"
    mock_property.is_deleted = False
    mock_property_repo.get.return_value = mock_property

    mock_booking = MagicMock()
    mock_booking.id = booking_id
    mock_booking.student_id = student_id
    mock_booking.bed_id = bed_id
    mock_booking.property_id = prop_id
    mock_booking.status = BookingStatus.CONFIRMED.value
    mock_booking.is_deleted = False
    mock_booking_repo.create.return_value = mock_booking
    mock_booking_repo.get_by_hold_request.return_value = None

    # Instantiate BookingService
    service = BookingService(
        booking_repo=mock_booking_repo,
        hold_repo=mock_hold_repo_async,
        bed_repo=mock_bed_repo,
        property_repo=mock_property_repo,
        waitlist_service=mock_waitlist_service,
        notification_service=mock_notification_service,
        audit_service=mock_audit_service,
        user_repo=mock_user_repo,
    )

    # Call method
    await service.create_from_hold(
        hold_id=hold_id,
        owner_id=owner_id,
        ip_address="127.0.0.1",
        user_agent="TestAgent",
    )

    # Assert audit service was invoked with booking info
    mock_audit_service.log_action.assert_called_once()
    call_kwargs = mock_audit_service.log_action.call_args.kwargs
    assert call_kwargs["action"] == "booking_confirmed"
    assert call_kwargs["entity_type"] == "booking"
    assert call_kwargs["entity_id"] == mock_booking.id
    assert call_kwargs["user_id"] == owner_id
    assert call_kwargs["new_data"] == {
        "bed_id": str(bed_id),
        "student_id": str(student_id),
        "hold_request_id": str(hold_id),
        "source": "hold_conversion",
    }
    assert call_kwargs["ip_address"] == "127.0.0.1"
    assert call_kwargs["user_agent"] == "TestAgent"

