"""Notification repository — data access for the ``notifications`` table.

Standalone repository (not extending ``BaseRepository``) because
``Notification`` inherits from ``Base`` (no ``updated_at`` / ``deleted_at``).
Notifications are immutable after creation — only ``is_read`` and
``read_at`` are updated.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import NotificationType
from app.models.notification import Notification


class NotificationRepository:
    """Data access layer for the ``notifications`` table.

    Uses insert-then-update-read-only semantics (no soft-delete).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Create ───────────────────────────────────────────────────────────────

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        type: NotificationType,
        title: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> Notification:
        """Insert a new notification record.

        Args:
            user_id: Recipient user UUID.
            type:    Notification type enum.
            title:   Short title for the notification bell.
            message: Full notification body.
            data:    Optional JSONB payload for UI rendering.

        Returns:
            The newly created and refreshed Notification instance.
        """
        instance = Notification(
            user_id=user_id,
            type=type.value,
            title=title,
            message=message,
            data=data or {},
        )
        self._session.add(instance)
        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    async def bulk_create(
        self, notifications: list[dict[str, Any]]
    ) -> list[Notification]:
        """Insert multiple notifications in a single flush.

        Args:
            notifications: List of dicts with keys: user_id, type, title,
                           message, data (optional).

        Returns:
            List of created Notification instances.
        """
        instances = []
        for n in notifications:
            instance = Notification(
                user_id=n["user_id"],
                type=n["type"].value if isinstance(n["type"], NotificationType) else n["type"],
                title=n["title"],
                message=n["message"],
                data=n.get("data", {}),
            )
            self._session.add(instance)
            instances.append(instance)
        await self._session.flush()
        for inst in instances:
            await self._session.refresh(inst)
        return instances

    # ── Read ─────────────────────────────────────────────────────────────────

    async def get(self, notification_id: uuid.UUID) -> Notification | None:
        """Fetch a single notification by primary key."""
        stmt = select(Notification).where(Notification.id == notification_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        *,
        unread_only: bool = False,
        notification_type: NotificationType | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Notification], int]:
        """Paginated notifications for a user.

        Args:
            user_id:           Target user.
            unread_only:       If True, return only unread notifications.
            notification_type: Optional filter by notification type.
            page:              1-indexed page number.
            page_size:         Items per page.

        Returns:
            Tuple of (items, total_count).
        """
        base = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            base = base.where(Notification.is_read.is_(False))
        if notification_type is not None:
            base = base.where(Notification.type == notification_type.value)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            base.order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def count_unread(self, user_id: uuid.UUID) -> int:
        """Count unread notifications for a user (badge count)."""
        stmt = (
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.is_read.is_(False))
        )
        return (await self._session.execute(stmt)).scalar() or 0

    # ── Mark as read ─────────────────────────────────────────────────────────

    async def mark_as_read(
        self, notification_id: uuid.UUID
    ) -> Notification | None:
        """Mark a single notification as read.

        Returns the updated record, or ``None`` if not found.
        """
        now = datetime.now(tz=timezone.utc)
        stmt = (
            update(Notification)
            .where(Notification.id == notification_id)
            .where(Notification.is_read.is_(False))
            .values(is_read=True, read_at=now)
            .returning(Notification)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_all_as_read(self, user_id: uuid.UUID) -> int:
        """Mark all unread notifications for a user as read.

        Returns the number of notifications marked.
        """
        now = datetime.now(tz=timezone.utc)
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.is_read.is_(False))
            .values(is_read=True, read_at=now)
        )
        result = await self._session.execute(stmt)
        return result.rowcount

    # ── Delete ───────────────────────────────────────────────────────────────

    async def delete_all_for_user(self, user_id: uuid.UUID) -> int:
        """Delete all notifications for a user.

        Returns the number of notifications deleted.
        """
        from sqlalchemy import delete
        stmt = delete(Notification).where(Notification.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.rowcount
