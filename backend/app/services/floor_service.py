"""Floor service — business logic for floor CRUD.

Validates property ownership before any floor mutation.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException
from app.repositories.floor_repository import FloorRepository
from app.repositories.property_repository import PropertyRepository
from app.schemas.floor import FloorCreate, FloorUpdate


class FloorService:
    """Orchestrates floor business logic.

    Args:
        floor_repo:    Repository for floors table.
        property_repo: Repository for properties table (ownership checks).
    """

    def __init__(
        self,
        floor_repo: FloorRepository,
        property_repo: PropertyRepository,
    ) -> None:
        self._floor_repo = floor_repo
        self._property_repo = property_repo

    async def create_floor(
        self,
        property_id: uuid.UUID,
        owner_id: uuid.UUID,
        data: FloorCreate,
        db: AsyncSession,
    ):
        """Create a floor within a property (ownership check included).

        Returns the created Floor.
        """
        await self._verify_property_ownership(property_id, owner_id)

        floor = await self._floor_repo.create(
            property_id=property_id,
            floor_number=data.floor_number,
            name=data.name,
            description=data.description,
            sort_order=data.sort_order,
        )
        await db.commit()
        await db.refresh(floor)
        return floor

    async def update_floor(
        self,
        floor_id: uuid.UUID,
        owner_id: uuid.UUID,
        data: FloorUpdate,
        db: AsyncSession,
    ):
        """Update a floor (ownership check via parent property).

        Returns the updated Floor.
        """
        floor = await self._get_floor(floor_id)
        await self._verify_property_ownership(floor.property_id, owner_id)

        update_data = data.model_dump(exclude_unset=True)
        if update_data:
            await self._floor_repo.update(floor_id, **update_data)
            await db.commit()
            await db.refresh(floor)

        return floor

    async def delete_floor(
        self,
        floor_id: uuid.UUID,
        owner_id: uuid.UUID,
        db: AsyncSession,
    ) -> None:
        """Soft-delete a floor (ownership check via parent property)."""
        floor = await self._get_floor(floor_id)
        await self._verify_property_ownership(floor.property_id, owner_id)
        await self._floor_repo.soft_delete(floor_id)
        await db.commit()

    async def list_floors(self, property_id: uuid.UUID):
        """List all floors for a property."""
        return await self._floor_repo.list_by_property(property_id)

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _get_floor(self, floor_id: uuid.UUID):
        """Fetch a floor, raising NotFoundException if missing."""
        floor = await self._floor_repo.get(floor_id)
        if floor is None or floor.is_deleted:
            raise NotFoundException(
                message="Floor not found.",
                code="FLOOR_NOT_FOUND",
            )
        return floor

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
