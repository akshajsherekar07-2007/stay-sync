"""Property service — business logic for property CRUD.

Handles property creation, update, deletion, status transitions,
amenity management, and ownership validation.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from app.models.property_amenity import PropertyAmenity
from app.repositories.amenity_repository import AmenityRepository
from app.repositories.property_repository import PropertyRepository
from app.repositories.saved_property_repository import SavedPropertyRepository
from app.schemas.amenity import AmenityAttach
from app.schemas.property import (
    PropertyCreate,
    PropertyFilter,
    PropertyStatusUpdate,
    PropertyUpdate,
)


class PropertyService:
    """Orchestrates property business logic.

    Args:
        property_repo: Repository for properties table.
        amenity_repo:  Repository for amenities table.
        saved_repo:    Repository for saved_properties table.
    """

    def __init__(
        self,
        property_repo: PropertyRepository,
        amenity_repo: AmenityRepository,
        saved_repo: SavedPropertyRepository,
    ) -> None:
        self._property_repo = property_repo
        self._amenity_repo = amenity_repo
        self._saved_repo = saved_repo

    # ── CRUD ──────────────────────────────────────────────────────────────────

    async def create_property(
        self,
        owner_id: uuid.UUID,
        data: PropertyCreate,
        db: AsyncSession,
    ):
        """Create a new property in draft status.

        Returns the created Property ORM instance.
        """
        prop = await self._property_repo.create(
            owner_id=owner_id,
            name=data.name,
            description=data.description,
            property_type=data.property_type.value,
            gender_preference=data.gender_preference.value,
            address_line1=data.address_line1,
            address_line2=data.address_line2,
            city=data.city,
            state=data.state,
            pincode=data.pincode,
            country=data.country,
            latitude=data.latitude,
            longitude=data.longitude,
            google_place_id=data.google_place_id,
            place_name=data.place_name,
            contact_phone=data.contact_phone,
            contact_email=data.contact_email,
            rules=data.rules,
            status="draft",
        )
        await db.commit()
        await db.refresh(prop)
        return prop

    async def update_property(
        self,
        property_id: uuid.UUID,
        owner_id: uuid.UUID,
        data: PropertyUpdate,
        db: AsyncSession,
    ):
        """Update a property (ownership check included).

        Returns the updated Property.
        """
        prop = await self._get_owned_property(property_id, owner_id)

        update_data = data.model_dump(exclude_unset=True)
        # Convert enum values to strings
        if "property_type" in update_data and update_data["property_type"] is not None:
            update_data["property_type"] = update_data["property_type"].value
        if "gender_preference" in update_data and update_data["gender_preference"] is not None:
            update_data["gender_preference"] = update_data["gender_preference"].value

        if update_data:
            await self._property_repo.update(property_id, **update_data)
            await db.commit()
            await db.refresh(prop)

        return prop

    async def delete_property(
        self,
        property_id: uuid.UUID,
        owner_id: uuid.UUID,
        db: AsyncSession,
    ) -> None:
        """Soft-delete a property (ownership check included)."""
        await self._get_owned_property(property_id, owner_id)
        await self._property_repo.soft_delete(property_id)
        await db.commit()

    async def get_property(self, property_id: uuid.UUID):
        """Fetch a single property by ID.

        Raises NotFoundException if not found or deleted.
        """
        prop = await self._property_repo.get(property_id)
        if prop is None or prop.is_deleted:
            raise NotFoundException(
                message="Property not found.",
                code="PROPERTY_NOT_FOUND",
            )
        return prop

    async def get_property_detail(self, property_id: uuid.UUID):
        """Fetch a property with full hierarchy (floors/rooms/beds/amenities/images).

        Raises NotFoundException if not found.
        """
        prop = await self._property_repo.get_detail(property_id)
        if prop is None:
            raise NotFoundException(
                message="Property not found.",
                code="PROPERTY_NOT_FOUND",
            )
        return prop

    async def list_properties(
        self,
        filters: PropertyFilter,
    ) -> tuple[list, int]:
        """Fetch a paginated, filtered list of properties.

        Returns (items, total_count).
        """
        return await self._property_repo.list_filtered(filters)

    async def list_owner_properties(self, owner_id: uuid.UUID):
        """Fetch all properties belonging to an owner."""
        return await self._property_repo.get_by_owner(owner_id)

    # ── Status ────────────────────────────────────────────────────────────────

    async def update_status(
        self,
        property_id: uuid.UUID,
        owner_id: uuid.UUID,
        data: PropertyStatusUpdate,
        db: AsyncSession,
    ):
        """Change property status (ownership check included).

        Returns the updated Property.
        """
        prop = await self._get_owned_property(property_id, owner_id)
        await self._property_repo.update(property_id, status=data.status.value)
        await db.commit()
        await db.refresh(prop)
        return prop

    async def refresh_property(
        self,
        property_id: uuid.UUID,
        owner_id: uuid.UUID,
        db: AsyncSession,
    ):
        """Update the last_refreshed_at timestamp (ownership check included).

        Returns the updated Property.
        """
        prop = await self._get_owned_property(property_id, owner_id)
        await self._property_repo.update(
            property_id,
            last_refreshed_at=datetime.now(tz=timezone.utc),
        )
        await db.commit()
        await db.refresh(prop)
        return prop

    # ── Amenities ─────────────────────────────────────────────────────────────

    async def attach_amenities(
        self,
        property_id: uuid.UUID,
        owner_id: uuid.UUID,
        data: AmenityAttach,
        db: AsyncSession,
    ) -> list:
        """Attach amenities to a property (ownership check included).

        Validates that all amenity IDs exist. Skips duplicates silently.
        Returns the list of attached amenity IDs.
        """
        await self._get_owned_property(property_id, owner_id)

        # Validate all amenity IDs exist
        found = await self._amenity_repo.get_by_ids(data.amenity_ids)
        found_ids = {a.id for a in found}
        missing = [aid for aid in data.amenity_ids if aid not in found_ids]
        if missing:
            raise BadRequestException(
                message=f"Amenity IDs not found: {[str(m) for m in missing]}",
                code="AMENITY_NOT_FOUND",
            )

        # Check which are already attached
        existing_stmt = (
            select(PropertyAmenity.amenity_id)
            .where(PropertyAmenity.property_id == property_id)
            .where(PropertyAmenity.amenity_id.in_(data.amenity_ids))
        )
        result = await db.execute(existing_stmt)
        existing_ids = {row[0] for row in result.all()}

        # Insert new ones
        for amenity_id in data.amenity_ids:
            if amenity_id not in existing_ids:
                db.add(
                    PropertyAmenity(
                        property_id=property_id,
                        amenity_id=amenity_id,
                    )
                )

        await db.commit()
        return data.amenity_ids

    async def detach_amenity(
        self,
        property_id: uuid.UUID,
        amenity_id: uuid.UUID,
        owner_id: uuid.UUID,
        db: AsyncSession,
    ) -> None:
        """Remove an amenity from a property (ownership check included)."""
        await self._get_owned_property(property_id, owner_id)

        stmt = (
            delete(PropertyAmenity)
            .where(PropertyAmenity.property_id == property_id)
            .where(PropertyAmenity.amenity_id == amenity_id)
        )
        result = await db.execute(stmt)
        if result.rowcount == 0:
            raise NotFoundException(
                message="Amenity is not attached to this property.",
                code="AMENITY_NOT_ATTACHED",
            )
        await db.commit()

    # ── Saved / Wishlist ──────────────────────────────────────────────────────

    async def save_property(
        self,
        student_id: uuid.UUID,
        property_id: uuid.UUID,
        db: AsyncSession,
    ) -> None:
        """Save a property to a student's wishlist."""
        # Verify property exists
        await self.get_property(property_id)

        already_saved = await self._saved_repo.is_saved(student_id, property_id)
        if already_saved:
            raise BadRequestException(
                message="Property is already saved.",
                code="ALREADY_SAVED",
            )

        await self._saved_repo.save(student_id, property_id)
        await db.commit()

    async def unsave_property(
        self,
        student_id: uuid.UUID,
        property_id: uuid.UUID,
        db: AsyncSession,
    ) -> None:
        """Remove a property from a student's wishlist."""
        removed = await self._saved_repo.unsave(student_id, property_id)
        if not removed:
            raise NotFoundException(
                message="Property is not in your saved list.",
                code="NOT_SAVED",
            )
        await db.commit()

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _get_owned_property(self, property_id: uuid.UUID, owner_id: uuid.UUID):
        """Fetch a property and verify ownership.

        Raises NotFoundException or ForbiddenException.
        """
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
        return prop
