"""Image repository — data access for the ``property_images`` table."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.property_image import PropertyImage


class ImageRepository:
    """Data access layer for the ``property_images`` table.

    Does not extend BaseRepository because PropertyImage has different
    timestamp columns (no updated_at).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **kwargs: Any) -> PropertyImage:
        """Create and persist a new image record."""
        instance = PropertyImage(**kwargs)
        self._session.add(instance)
        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    async def get(self, image_id: uuid.UUID) -> PropertyImage | None:
        """Fetch a single non-deleted image by ID."""
        stmt = (
            select(PropertyImage)
            .where(PropertyImage.id == image_id)
            .where(PropertyImage.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_property(self, property_id: uuid.UUID) -> list[PropertyImage]:
        """Fetch all non-deleted images for a property."""
        stmt = (
            select(PropertyImage)
            .where(PropertyImage.property_id == property_id)
            .where(PropertyImage.deleted_at.is_(None))
            .order_by(PropertyImage.sort_order)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_entity(
        self, entity_type: str, entity_id: uuid.UUID
    ) -> list[PropertyImage]:
        """Fetch all non-deleted images for a specific entity."""
        stmt = (
            select(PropertyImage)
            .where(PropertyImage.entity_type == entity_type)
            .where(PropertyImage.entity_id == entity_id)
            .where(PropertyImage.deleted_at.is_(None))
            .order_by(PropertyImage.sort_order)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_property(self, property_id: uuid.UUID) -> int:
        """Count non-deleted images for a property."""
        from sqlalchemy import func

        stmt = (
            select(func.count())
            .select_from(PropertyImage)
            .where(PropertyImage.property_id == property_id)
            .where(PropertyImage.deleted_at.is_(None))
        )
        return (await self._session.execute(stmt)).scalar() or 0

    async def soft_delete(self, image_id: uuid.UUID) -> bool:
        """Soft-delete an image by setting deleted_at."""
        stmt = (
            update(PropertyImage)
            .where(PropertyImage.id == image_id)
            .where(PropertyImage.deleted_at.is_(None))
            .values(deleted_at=datetime.now(tz=timezone.utc))
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def set_primary(
        self, image_id: uuid.UUID, property_id: uuid.UUID
    ) -> None:
        """Set an image as primary, unsetting any current primary for the property."""
        # Unset current primary
        await self._session.execute(
            update(PropertyImage)
            .where(PropertyImage.property_id == property_id)
            .where(PropertyImage.deleted_at.is_(None))
            .where(PropertyImage.is_primary.is_(True))
            .values(is_primary=False)
        )
        # Set new primary
        await self._session.execute(
            update(PropertyImage)
            .where(PropertyImage.id == image_id)
            .values(is_primary=True)
        )

    async def update_sort_orders(
        self, reorder_items: list[dict[str, Any]]
    ) -> None:
        """Batch update sort_order for multiple images.

        Args:
            reorder_items: List of {"id": uuid, "sort_order": int} dicts.
        """
        for item in reorder_items:
            await self._session.execute(
                update(PropertyImage)
                .where(PropertyImage.id == item["id"])
                .values(sort_order=item["sort_order"])
            )
