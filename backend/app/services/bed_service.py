"""Bed service — business logic for bed CRUD.

Validates property ownership through the room → property chain.
Bed counts are maintained by the DB trigger ``sync_property_bed_counts``.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException
from app.repositories.bed_repository import BedRepository
from app.repositories.property_repository import PropertyRepository
from app.repositories.room_repository import RoomRepository
from app.schemas.bed import BedCreate, BedUpdate


class BedService:
    """Orchestrates bed business logic.

    Args:
        bed_repo:      Repository for beds table.
        room_repo:     Repository for rooms table.
        property_repo: Repository for properties table.
    """

    def __init__(
        self,
        bed_repo: BedRepository,
        room_repo: RoomRepository,
        property_repo: PropertyRepository,
    ) -> None:
        self._bed_repo = bed_repo
        self._room_repo = room_repo
        self._property_repo = property_repo

    async def create_bed(
        self,
        room_id: uuid.UUID,
        owner_id: uuid.UUID,
        data: BedCreate,
        db: AsyncSession,
    ):
        """Create a bed within a room (ownership check included).

        Returns the created Bed.
        """
        room = await self._get_room(room_id)
        await self._verify_property_ownership(room.property_id, owner_id)

        bed = await self._bed_repo.create(
            room_id=room_id,
            property_id=room.property_id,
            bed_number=data.bed_number,
            label=data.label,
            price=data.price,
            sort_order=data.sort_order,
            status="vacant",
        )
        await db.commit()
        await db.refresh(bed)
        return bed

    async def update_bed(
        self,
        bed_id: uuid.UUID,
        owner_id: uuid.UUID,
        data: BedUpdate,
        db: AsyncSession,
    ):
        """Update a bed (ownership check via property).

        Returns the updated Bed.
        """
        bed = await self._get_bed(bed_id)
        await self._verify_property_ownership(bed.property_id, owner_id)

        update_data = data.model_dump(exclude_unset=True)
        if update_data:
            await self._bed_repo.update(bed_id, **update_data)
            await db.commit()
            await db.refresh(bed)

        return bed

    async def delete_bed(
        self,
        bed_id: uuid.UUID,
        owner_id: uuid.UUID,
        db: AsyncSession,
    ) -> None:
        """Soft-delete a bed (ownership check via property).

        The DB trigger will automatically update property bed counts.
        """
        bed = await self._get_bed(bed_id)
        await self._verify_property_ownership(bed.property_id, owner_id)
        await self._bed_repo.soft_delete(bed_id)
        await db.commit()

    async def list_beds(self, room_id: uuid.UUID):
        """List all beds for a room."""
        return await self._bed_repo.list_by_room(room_id)

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _get_bed(self, bed_id: uuid.UUID):
        """Fetch a bed, raising NotFoundException if missing."""
        bed = await self._bed_repo.get(bed_id)
        if bed is None or bed.is_deleted:
            raise NotFoundException(
                message="Bed not found.",
                code="BED_NOT_FOUND",
            )
        return bed

    async def _get_room(self, room_id: uuid.UUID):
        """Fetch a room, raising NotFoundException if missing."""
        room = await self._room_repo.get(room_id)
        if room is None or room.is_deleted:
            raise NotFoundException(
                message="Room not found.",
                code="ROOM_NOT_FOUND",
            )
        return room

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
