"""Room service — business logic for room CRUD.

Validates property ownership through the floor → property chain.
Recalculates property price range after room mutations.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException
from app.repositories.floor_repository import FloorRepository
from app.repositories.property_repository import PropertyRepository
from app.repositories.room_repository import RoomRepository
from app.schemas.room import RoomCreate, RoomUpdate


class RoomService:
    """Orchestrates room business logic.

    Args:
        room_repo:     Repository for rooms table.
        floor_repo:    Repository for floors table.
        property_repo: Repository for properties table.
    """

    def __init__(
        self,
        room_repo: RoomRepository,
        floor_repo: FloorRepository,
        property_repo: PropertyRepository,
    ) -> None:
        self._room_repo = room_repo
        self._floor_repo = floor_repo
        self._property_repo = property_repo

    async def create_room(
        self,
        floor_id: uuid.UUID,
        owner_id: uuid.UUID,
        data: RoomCreate,
        db: AsyncSession,
    ):
        """Create a room within a floor (ownership check included).

        Returns the created Room.
        """
        floor = await self._get_floor(floor_id)
        await self._verify_property_ownership(floor.property_id, owner_id)

        room = await self._room_repo.create(
            floor_id=floor_id,
            property_id=floor.property_id,
            room_number=data.room_number,
            name=data.name,
            sharing_type=data.sharing_type.value,
            price_per_bed=data.price_per_bed,
            description=data.description,
            has_attached_bath=data.has_attached_bath,
            has_ac=data.has_ac,
            has_balcony=data.has_balcony,
            sort_order=data.sort_order,
        )
        await db.commit()
        await db.refresh(room)

        # Recalculate property price range
        await self._property_repo.update_price_range(floor.property_id)
        await db.commit()

        return room

    async def update_room(
        self,
        room_id: uuid.UUID,
        owner_id: uuid.UUID,
        data: RoomUpdate,
        db: AsyncSession,
    ):
        """Update a room (ownership check via property).

        Returns the updated Room.
        """
        room = await self._get_room(room_id)
        await self._verify_property_ownership(room.property_id, owner_id)

        update_data = data.model_dump(exclude_unset=True)
        if "sharing_type" in update_data and update_data["sharing_type"] is not None:
            update_data["sharing_type"] = update_data["sharing_type"].value

        if update_data:
            await self._room_repo.update(room_id, **update_data)
            await db.commit()
            await db.refresh(room)

            # Recalculate price range if price changed
            if "price_per_bed" in update_data:
                await self._property_repo.update_price_range(room.property_id)
                await db.commit()

        return room

    async def delete_room(
        self,
        room_id: uuid.UUID,
        owner_id: uuid.UUID,
        db: AsyncSession,
    ) -> None:
        """Soft-delete a room (ownership check via property)."""
        room = await self._get_room(room_id)
        await self._verify_property_ownership(room.property_id, owner_id)

        property_id = room.property_id
        await self._room_repo.soft_delete(room_id)
        await db.commit()

        # Recalculate property price range
        await self._property_repo.update_price_range(property_id)
        await db.commit()

    async def list_rooms(self, floor_id: uuid.UUID):
        """List all rooms for a floor."""
        return await self._room_repo.list_by_floor(floor_id)

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _get_room(self, room_id: uuid.UUID):
        """Fetch a room, raising NotFoundException if missing."""
        room = await self._room_repo.get(room_id)
        if room is None or room.is_deleted:
            raise NotFoundException(
                message="Room not found.",
                code="ROOM_NOT_FOUND",
            )
        return room

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
