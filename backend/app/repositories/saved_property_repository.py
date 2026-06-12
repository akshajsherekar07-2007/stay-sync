"""SavedProperty repository — data access for the ``saved_properties`` table."""

from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.property import Property
from app.models.saved_property import SavedProperty


class SavedPropertyRepository:
    """Data access layer for the ``saved_properties`` table.

    Uses hard-delete semantics (no deleted_at column).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(
        self, student_id: uuid.UUID, property_id: uuid.UUID
    ) -> SavedProperty:
        """Save a property to the student's wishlist.

        Raises IntegrityError if already saved (unique constraint).
        """
        instance = SavedProperty(student_id=student_id, property_id=property_id)
        self._session.add(instance)
        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    async def unsave(
        self, student_id: uuid.UUID, property_id: uuid.UUID
    ) -> bool:
        """Remove a property from the student's wishlist.

        Returns True if a row was deleted.
        """
        stmt = (
            delete(SavedProperty)
            .where(SavedProperty.student_id == student_id)
            .where(SavedProperty.property_id == property_id)
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def is_saved(
        self, student_id: uuid.UUID, property_id: uuid.UUID
    ) -> bool:
        """Check if a property is saved by a student."""
        stmt = (
            select(func.count())
            .select_from(SavedProperty)
            .where(SavedProperty.student_id == student_id)
            .where(SavedProperty.property_id == property_id)
        )
        count = (await self._session.execute(stmt)).scalar() or 0
        return count > 0

    async def list_by_student(
        self, student_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> tuple[list[uuid.UUID], int]:
        """Fetch paginated saved property IDs for a student.

        Returns:
            Tuple of (property_id_list, total_count).
        """
        base = select(SavedProperty).where(
            SavedProperty.student_id == student_id
        )

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            base.order_by(SavedProperty.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        items = [row.property_id for row in result.scalars().all()]

        return items, total
