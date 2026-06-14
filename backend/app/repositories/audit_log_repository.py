"""AuditLog repository — data access for the ``audit_logs`` table.

Standalone repository (not extending ``BaseRepository``) because
``AuditLog`` inherits from ``Base`` (no ``updated_at`` / ``deleted_at``).
Audit logs are strictly append-only — no updates or deletes.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditLogRepository:
    """Data access layer for the ``audit_logs`` table.

    Append-only — no update or delete methods.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Create ───────────────────────────────────────────────────────────────

    async def create(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
        old_data: dict[str, Any] | None = None,
        new_data: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Insert a new audit log entry.

        Args:
            action:      Action performed (e.g. 'hold_approved').
            entity_type: Type of entity affected (e.g. 'hold_request').
            entity_id:   UUID of the affected entity.
            user_id:     Actor user UUID (None for system-initiated).
            old_data:    JSONB snapshot before the change.
            new_data:    JSONB snapshot after the change.
            ip_address:  Client IP at time of action.
            user_agent:  Client user-agent string.

        Returns:
            The newly created and refreshed AuditLog instance.
        """
        instance = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_data=old_data,
            new_data=new_data,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._session.add(instance)
        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    # ── Read ─────────────────────────────────────────────────────────────────

    async def get(self, log_id: uuid.UUID) -> AuditLog | None:
        """Fetch a single audit log entry by primary key."""
        stmt = select(AuditLog).where(AuditLog.id == log_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # ── List queries ─────────────────────────────────────────────────────────

    async def list_by_entity(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """Paginated audit trail for a specific entity.

        Returns:
            Tuple of (items, total_count).
        """
        base = (
            select(AuditLog)
            .where(AuditLog.entity_type == entity_type)
            .where(AuditLog.entity_id == entity_id)
        )

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            base.order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """Paginated audit logs for actions performed by a user.

        Returns:
            Tuple of (items, total_count).
        """
        base = select(AuditLog).where(AuditLog.user_id == user_id)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            base.order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def list_by_action(
        self,
        action: str,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """Paginated audit logs filtered by action type.

        Returns:
            Tuple of (items, total_count).
        """
        base = select(AuditLog).where(AuditLog.action == action)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            base.order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def list_by_entity_type(
        self,
        entity_type: str,
        *,
        since: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """Paginated audit logs for all entities of a given type.

        Args:
            entity_type: The entity type to filter by (e.g. 'hold_request').
            since:       Optional lower-bound timestamp filter.
            page:        1-indexed page number.
            page_size:   Items per page.

        Returns:
            Tuple of (items, total_count).
        """
        base = select(AuditLog).where(AuditLog.entity_type == entity_type)
        if since is not None:
            base = base.where(AuditLog.created_at >= since)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            base.order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def count_by_action(
        self, action: str, entity_id: uuid.UUID | None = None
    ) -> int:
        """Count audit log entries for an action, optionally scoped to an entity.

        Useful for tracking how many times an action occurred.
        """
        stmt = (
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.action == action)
        )
        if entity_id is not None:
            stmt = stmt.where(AuditLog.entity_id == entity_id)
        return (await self._session.execute(stmt)).scalar() or 0
