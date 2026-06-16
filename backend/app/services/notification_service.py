"""Notification service — business logic for in-app notifications.

Provides helpers to create domain-specific notifications for hold,
booking, and waitlist events, plus read-state management.

Phase 2 transaction convention: this service only ``flush()``es.
The calling router is responsible for ``commit()``.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from app.core.enums import NotificationType
from app.models.notification import Notification
from app.repositories.notification_repository import NotificationRepository

logger = logging.getLogger(__name__)


class NotificationService:
    """Orchestrates in-app notification creation and management."""

    def __init__(self, notification_repo: NotificationRepository) -> None:
        self._notification_repo = notification_repo

    # ── Domain-specific notification creators ────────────────────────────────

    async def notify_hold_requested(
        self,
        *,
        owner_id: uuid.UUID,
        student_id: uuid.UUID,
        bed_id: uuid.UUID,
        property_name: str,
        bed_label: str,
    ) -> Notification:
        """Notify the property owner that a hold was requested."""
        return await self._notification_repo.create(
            user_id=owner_id,
            type=NotificationType.HOLD_REQUESTED,
            title="New Hold Request",
            message=f"A student has requested a hold on bed {bed_label} in {property_name}.",
            data={
                "student_id": str(student_id),
                "bed_id": str(bed_id),
            },
        )

    async def notify_hold_approved(
        self,
        *,
        student_id: uuid.UUID,
        bed_id: uuid.UUID,
        property_name: str,
        bed_label: str,
        expires_at: str,
    ) -> Notification:
        """Notify the student their hold was approved."""
        return await self._notification_repo.create(
            user_id=student_id,
            type=NotificationType.HOLD_APPROVED,
            title="Hold Approved",
            message=(
                f"Your hold on bed {bed_label} in {property_name} has been approved. "
                f"It expires at {expires_at}."
            ),
            data={
                "bed_id": str(bed_id),
                "expires_at": expires_at,
            },
        )

    async def notify_hold_rejected(
        self,
        *,
        student_id: uuid.UUID,
        bed_id: uuid.UUID,
        property_name: str,
        bed_label: str,
        resolution_note: str | None = None,
    ) -> Notification:
        """Notify the student their hold was rejected."""
        msg = f"Your hold on bed {bed_label} in {property_name} has been rejected."
        if resolution_note:
            msg += f" Reason: {resolution_note}"
        return await self._notification_repo.create(
            user_id=student_id,
            type=NotificationType.HOLD_REJECTED,
            title="Hold Rejected",
            message=msg,
            data={"bed_id": str(bed_id)},
        )

    async def notify_hold_expired(
        self,
        *,
        student_id: uuid.UUID,
        bed_id: uuid.UUID,
        property_name: str,
        bed_label: str,
    ) -> Notification:
        """Notify the student their hold expired."""
        return await self._notification_repo.create(
            user_id=student_id,
            type=NotificationType.HOLD_EXPIRED,
            title="Hold Expired",
            message=f"Your hold on bed {bed_label} in {property_name} has expired.",
            data={"bed_id": str(bed_id)},
        )

    async def notify_hold_expiring_soon(
        self,
        *,
        student_id: uuid.UUID,
        bed_id: uuid.UUID,
        property_name: str,
        bed_label: str,
        expires_at: str,
    ) -> Notification:
        """Notify the student their hold is expiring soon."""
        return await self._notification_repo.create(
            user_id=student_id,
            type=NotificationType.HOLD_EXPIRING_SOON,
            title="Hold Expiring Soon",
            message=(
                f"Your hold on bed {bed_label} in {property_name} expires at "
                f"{expires_at}. Please complete your booking or extend."
            ),
            data={
                "bed_id": str(bed_id),
                "expires_at": expires_at,
            },
        )

    async def notify_hold_overridden(
        self,
        *,
        student_id: uuid.UUID,
        bed_id: uuid.UUID,
        property_name: str,
        bed_label: str,
    ) -> Notification:
        """Notify the original student their hold was overridden by the owner."""
        return await self._notification_repo.create(
            user_id=student_id,
            type=NotificationType.HOLD_OVERRIDDEN,
            title="Hold Overridden",
            message=(
                f"Your hold on bed {bed_label} in {property_name} has been "
                f"overridden by the property owner."
            ),
            data={"bed_id": str(bed_id)},
        )

    async def notify_waitlist_promoted(
        self,
        *,
        student_id: uuid.UUID,
        bed_id: uuid.UUID,
        property_name: str,
        bed_label: str,
        expires_at: str,
    ) -> Notification:
        """Notify the promoted student they got a hold from the waitlist."""
        return await self._notification_repo.create(
            user_id=student_id,
            type=NotificationType.WAITLIST_PROMOTED,
            title="You've Been Promoted from the Waitlist",
            message=(
                f"A hold on bed {bed_label} in {property_name} has been "
                f"automatically approved for you. It expires at {expires_at}."
            ),
            data={
                "bed_id": str(bed_id),
                "expires_at": expires_at,
            },
        )

    async def notify_booking_confirmed(
        self,
        *,
        student_id: uuid.UUID,
        bed_id: uuid.UUID,
        property_name: str,
        bed_label: str,
    ) -> Notification:
        """Notify the student their booking is confirmed."""
        return await self._notification_repo.create(
            user_id=student_id,
            type=NotificationType.BOOKING_CONFIRMED,
            title="Booking Confirmed",
            message=f"Your booking for bed {bed_label} in {property_name} is confirmed.",
            data={"bed_id": str(bed_id)},
        )

    # ── Read-state management ────────────────────────────────────────────────

    async def list_notifications(
        self,
        user_id: uuid.UUID,
        *,
        unread_only: bool = False,
        notification_type: NotificationType | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Notification], int]:
        """Paginated notifications for a user."""
        return await self._notification_repo.list_by_user(
            user_id,
            unread_only=unread_only,
            notification_type=notification_type,
            page=page,
            page_size=page_size,
        )

    async def mark_as_read(self, notification_id: uuid.UUID) -> Notification | None:
        """Mark a single notification as read."""
        return await self._notification_repo.mark_as_read(notification_id)

    async def mark_all_as_read(self, user_id: uuid.UUID) -> int:
        """Mark all notifications as read for a user. Returns count marked."""
        return await self._notification_repo.mark_all_as_read(user_id)

    async def count_unread(self, user_id: uuid.UUID) -> int:
        """Unread notification count for badge display."""
        return await self._notification_repo.count_unread(user_id)
