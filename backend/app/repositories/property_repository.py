"""Property repository — data access for the ``properties`` table.

Extends ``BaseRepository[Property]`` with property-specific query methods
including filtered listing, owner-scoped queries, and detail loading.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.bed import Bed
from app.models.floor import Floor
from app.models.property import Property
from app.models.property_image import PropertyImage
from app.models.room import Room
from app.repositories.base import BaseRepository
from app.schemas.property import PropertyFilter


class PropertyRepository(BaseRepository[Property]):
    """Data access layer for the ``properties`` table."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Property)

    async def list_filtered(
        self,
        filters: PropertyFilter,
    ) -> tuple[list[Property], int]:
        """Fetch a paginated, filtered list of properties.

        Args:
            filters: Filter and pagination parameters.

        Returns:
            Tuple of (items, total_count).
        """
        stmt = (
            select(Property)
            .where(Property.deleted_at.is_(None))
        )

        # Dynamic WHERE clauses
        if filters.city:
            stmt = stmt.where(Property.city.ilike(f"%{filters.city}%"))
        if filters.state:
            stmt = stmt.where(Property.state.ilike(f"%{filters.state}%"))
        if filters.property_type:
            stmt = stmt.where(Property.property_type == filters.property_type.value)
        if filters.gender_preference:
            stmt = stmt.where(
                Property.gender_preference == filters.gender_preference.value
            )
        if filters.status:
            stmt = stmt.where(Property.status == filters.status.value)
        if filters.price_min is not None:
            stmt = stmt.where(Property.min_price >= filters.price_min)
        if filters.price_max is not None:
            stmt = stmt.where(Property.max_price <= filters.price_max)
        if filters.search:
            search_term = f"%{filters.search}%"
            stmt = stmt.where(Property.name.ilike(search_term))

        # Count query (before pagination)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar() or 0

        # Pagination
        offset = (filters.page - 1) * filters.page_size
        stmt = stmt.order_by(Property.created_at.desc())
        stmt = stmt.offset(offset).limit(filters.page_size)

        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_by_owner(self, owner_id: uuid.UUID) -> list[Property]:
        """Fetch all non-deleted properties for an owner.

        Args:
            owner_id: The owner's UUID.

        Returns:
            List of Property instances.
        """
        stmt = (
            select(Property)
            .where(Property.owner_id == owner_id)
            .where(Property.deleted_at.is_(None))
            .order_by(Property.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_detail(self, property_id: uuid.UUID) -> Property | None:
        """Fetch a property with eager-loaded hierarchy.

        Loads: floors → rooms → beds, property_amenities, images.

        Args:
            property_id: The property UUID.

        Returns:
            Fully loaded Property or None.
        """
        stmt = (
            select(Property)
            .options(
                selectinload(Property.floors)
                .selectinload(Floor.rooms)
                .selectinload(Room.beds),
                selectinload(Property.property_amenities),
                selectinload(Property.images),
            )
            .where(Property.id == property_id)
            .where(Property.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_by_owner(self, owner_id: uuid.UUID) -> int:
        """Count non-deleted properties for an owner."""
        stmt = (
            select(func.count())
            .select_from(Property)
            .where(Property.owner_id == owner_id)
            .where(Property.deleted_at.is_(None))
        )
        return (await self._session.execute(stmt)).scalar() or 0

    async def update_price_range(self, property_id: uuid.UUID) -> None:
        """Recalculate min_price and max_price from rooms and beds.

        Uses the effective price: bed.price if set, otherwise room.price_per_bed.
        """
        # Compute min/max from rooms
        price_stmt = (
            select(
                func.min(Room.price_per_bed).label("min_price"),
                func.max(Room.price_per_bed).label("max_price"),
            )
            .where(Room.property_id == property_id)
            .where(Room.deleted_at.is_(None))
        )
        result = await self._session.execute(price_stmt)
        row = result.one_or_none()

        min_price = row.min_price if row else None
        max_price = row.max_price if row else None

        await self._session.execute(
            update(Property)
            .where(Property.id == property_id)
            .values(min_price=min_price, max_price=max_price)
        )
